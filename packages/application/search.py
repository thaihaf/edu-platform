"""Phase 4 policy and deterministic use cases; no provider-specific parsing."""

from __future__ import annotations

import hashlib
import ipaddress
import posixpath
import re
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from uuid import UUID

from packages.domain.models import SourceSnapshot
from packages.domain.search import (
    FetchJob,
    FetchStage,
    FetchStatus,
    ProviderSearchResult,
    QueryStatus,
    SearchOptions,
    SearchQuery,
    SearchResult,
    SearchResultPage,
)
from packages.domain.search_ports import CrawlProvider, DNSResolver, SearchProvider


class SearchError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


TRACKING = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}
)


def canonicalize_web_url(value: str, remove_tracking: bool = True) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise SearchError("SEARCH_QUERY_INVALID", "URL is malformed") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise SearchError("SEARCH_QUERY_INVALID", "Only absolute HTTP(S) URLs are allowed")
    if parsed.username or parsed.password:
        raise SearchError("URL_HOST_FORBIDDEN", "URL credentials are not allowed")
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    port = parsed.port
    path = quote(unquote(parsed.path or "/"), safe="/%:@!$&'()*+,;=-._~")
    path = posixpath.normpath(path) if path != "/" else "/"
    if parsed.path.endswith("/") and path != "/":
        path += "/"
    query = "&".join(
        part
        for part in parsed.query.split("&")
        if not (remove_tracking and part.split("=", 1)[0].lower() in TRACKING)
    )
    netloc = (
        host
        if port is None
        or (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
        else f"{host}:{port}"
    )
    return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


async def validate_public_url(url: str, resolver: DNSResolver) -> str:
    canonical = canonicalize_web_url(url)
    host = urlsplit(canonical).hostname or ""
    if host == "localhost" or re.fullmatch(r"(?:0x[0-9a-f]+|\d+)", host, re.I):
        raise SearchError("URL_HOST_FORBIDDEN", "URL host is forbidden")
    try:
        addresses: tuple[str, ...] = (str(ipaddress.ip_address(host)),)
    except ValueError:
        try:
            addresses = await resolver.resolve(host)
        except Exception as exc:
            raise SearchError(
                "URL_RESOLUTION_FAILED", "URL hostname could not be resolved"
            ) from exc
    if not addresses:
        raise SearchError("URL_RESOLUTION_FAILED", "URL hostname could not be resolved")
    for raw in addresses:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError as exc:
            raise SearchError("URL_RESOLUTION_FAILED", "Resolver returned invalid address") from exc
        if not address.is_global or str(address) == "169.254.169.254":
            raise SearchError("URL_HOST_FORBIDDEN", "URL host is not publicly routable")
    return canonical


def normalize_result(
    item: ProviderSearchResult, query_id: UUID, provider: str, rank: int
) -> SearchResult:
    url = canonicalize_web_url(item.url)
    title = " ".join(item.title.split())
    snippet = " ".join(item.snippet.split())
    mime = item.content_type or ("application/pdf" if url.lower().endswith(".pdf") else "text/html")
    host = urlsplit(url).hostname or ""
    source_type = (
        "official"
        if host.startswith(("www.gov.", "gov.")) or host.endswith(".gov")
        else ("document" if "pdf" in mime else "other")
    )
    return SearchResult(
        query_id,
        provider,
        rank,
        rank,
        title,
        url,
        url,
        snippet,
        item.published_at,
        datetime.now().astimezone(),
        mime,
        1 / rank,
        source_type,
        metadata_json=dict(item.metadata),
    )


def reciprocal_rank_fusion(
    pages: dict[str, SearchResultPage], query_id: UUID, k: int = 60
) -> list[SearchResult]:
    clusters: dict[str, list[SearchResult]] = {}
    for provider, page in sorted(pages.items()):
        for rank, item in enumerate(page.results, 1):
            clusters.setdefault(canonicalize_web_url(item.url), []).append(
                normalize_result(item, query_id, provider, rank)
            )
    fused = []
    for _url, results in clusters.items():
        winner = min(results, key=lambda x: (x.provider_rank, x.provider))
        score = sum(1 / (k + x.provider_rank) for x in results)
        winner.relevance_score = score
        winner.metadata_json["provider_provenance"] = [
            {"provider": x.provider, "rank": x.provider_rank} for x in results
        ]
        fused.append(winner)
    return sorted(fused, key=lambda x: (-x.relevance_score, x.canonical_url))


@dataclass
class InMemorySearchRepository:
    queries: dict[UUID, SearchQuery] = field(default_factory=dict)
    results: dict[UUID, list[SearchResult]] = field(default_factory=dict)
    executions: dict[str, str] = field(default_factory=dict)


class SearchService:
    def __init__(self, repository: InMemorySearchRepository, providers: list[SearchProvider]):
        self.repository, self.providers = repository, providers

    async def register(self, query: SearchQuery) -> SearchQuery:
        if not query.query_text.strip() or query.max_results < 1:
            raise SearchError("SEARCH_QUERY_INVALID", "Query text and result limit are required")
        self.repository.queries[query.id] = query
        return query

    async def execute(self, query_id: UUID, idempotency_key: str) -> list[SearchResult]:
        query = self.repository.queries.get(query_id)
        if not query:
            raise SearchError("SEARCH_RESULT_NOT_FOUND", "Search query not found")
        payload = hashlib.sha256(
            f"{query_id}:{query.query_text}:{query.max_results}".encode()
        ).hexdigest()
        old = self.repository.executions.get(idempotency_key)
        if old and old != payload:
            raise SearchError("IDEMPOTENCY_CONFLICT", "Idempotency key payload differs")
        if old:
            return self.repository.results.get(query_id, [])
        self.repository.executions[idempotency_key] = payload
        query.status = QueryStatus.RUNNING
        try:
            pages = {
                p.provider_name: await p.search(
                    query.query_text,
                    SearchOptions(
                        locale=query.locale,
                        language=query.language,
                        result_limit=query.max_results,
                        domains_allowlist=query.domains_allowlist,
                        domains_denylist=query.domains_denylist,
                        file_types=query.file_types,
                    ),
                )
                for p in self.providers
            }
            values = reciprocal_rank_fusion(pages, query.id)[: query.max_results]
            for rank, value in enumerate(values, 1):
                value.normalized_rank = rank
            self.repository.results[query_id] = values
            query.status = QueryStatus.COMPLETED
            return values
        except SearchError:
            query.status = QueryStatus.FAILED
            raise


@dataclass
class InMemoryFetchRepository:
    """Durable-boundary test adapter; production adapters must make these writes transactional."""

    jobs: dict[UUID, FetchJob] = field(default_factory=dict)
    idempotency: dict[str, tuple[str, UUID]] = field(default_factory=dict)
    snapshots: dict[UUID, SourceSnapshot] = field(default_factory=dict)
    snapshot_jobs: dict[UUID, UUID] = field(default_factory=dict)

    async def create_job(self, job: FetchJob, request_hash: str) -> FetchJob:
        existing = self.idempotency.get(job.idempotency_key)
        if existing:
            if existing[0] != request_hash:
                raise SearchError("IDEMPOTENCY_CONFLICT", "Idempotency key payload differs")
            return self.jobs[existing[1]]
        self.jobs[job.id] = job
        self.idempotency[job.idempotency_key] = (request_hash, job.id)
        return job

    async def get_job(self, job_id: UUID) -> FetchJob | None:
        return self.jobs.get(job_id)

    async def update_job(self, job: FetchJob) -> None:
        self.jobs[job.id] = job

    async def snapshot_for_job(self, job_id: UUID) -> SourceSnapshot | None:
        snapshot_id = self.snapshot_jobs.get(job_id)
        return self.snapshots.get(snapshot_id) if snapshot_id else None

    async def create_snapshot(self, job_id: UUID, snapshot: SourceSnapshot) -> SourceSnapshot:
        existing = await self.snapshot_for_job(job_id)
        if existing:
            return existing
        self.snapshots[snapshot.id] = snapshot
        self.snapshot_jobs[job_id] = snapshot.id
        return snapshot


class FetchDispatcher:
    async def dispatch(self, job_id: UUID) -> None: ...


class FetchService:
    """Coordinates durable fetch-job transitions and immutable snapshot persistence."""

    def __init__(
        self,
        repository: InMemoryFetchRepository,
        crawler: CrawlProvider,
        dispatcher: FetchDispatcher,
    ):
        self.repository, self.crawler, self.dispatcher = repository, crawler, dispatcher

    async def accept(self, job: FetchJob) -> FetchJob:
        request_hash = hashlib.sha256(
            f"{job.project_id}:{job.source_id}:{job.canonical_url}".encode()
        ).hexdigest()
        persisted = await self.repository.create_job(job, request_hash)
        if persisted.id != job.id:  # idempotent replay: never dispatch again
            return persisted
        try:
            await self.dispatcher.dispatch(persisted.id)
        except Exception:
            self._fail(persisted, "DISPATCH_FAILED", "Crawler dispatch failed")
            await self.repository.update_job(persisted)
        return persisted

    async def run(self, job_id: UUID) -> FetchJob:
        job = await self.repository.get_job(job_id)
        if not job:
            raise SearchError("FETCH_JOB_NOT_FOUND", "Fetch job not found")
        if job.status is FetchStatus.COMPLETED:
            return job
        try:
            job.status, job.stage = FetchStatus.RUNNING, FetchStage.FETCHING
            job.started_at = job.started_at or datetime.now().astimezone()
            job.error_code = job.error_message = None
            await self.repository.update_job(job)
            document = await self.crawler.crawl_page(job.requested_url)
            job.stage = FetchStage.SNAPSHOTTING
            await self.repository.update_job(job)
            snapshot = await self.repository.snapshot_for_job(job.id)
            if not snapshot:
                snapshot = SourceSnapshot(
                    job.source_id,
                    1,
                    None,
                    document.raw_content_hash,
                    {"canonical_url": document.canonical_url, "fetch_job_id": str(job.id)},
                )
                await self.repository.create_snapshot(job.id, snapshot)
            job.status, job.stage = FetchStatus.COMPLETED, FetchStage.COMPLETED
            job.completed_at = datetime.now().astimezone()
            await self.repository.update_job(job)
        except SearchError as exc:
            self._fail(job, exc.code, str(exc))
            await self.repository.update_job(job)
        except Exception:
            self._fail(job, "SNAPSHOT_PERSISTENCE_FAILED", "Fetch processing failed")
            await self.repository.update_job(job)
        return job

    @staticmethod
    def _fail(job: FetchJob, code: str, message: str) -> None:
        job.status = FetchStatus.FAILED
        job.error_code, job.error_message = code, message
        job.failed_at = datetime.now().astimezone()
