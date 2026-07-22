from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from packages.application.ingestion import IngestionError, IngestionService, TextDocumentParser
from packages.application.search import InMemorySearchRepository, SearchError, SearchService
from packages.application.services import ConflictError, DomainService, NotFoundError
from packages.domain.models import (
    Course,
    CourseVersion,
    ProjectStatus,
    ResearchProject,
    Source,
    SourceSnapshot,
    Workspace,
)
from packages.domain.ports import ReadinessProbe
from packages.domain.search import FetchJob, FetchStage, FetchStatus, QueryFamily, SearchQuery
from packages.infrastructure.ingestion import (
    DeterministicEmbeddingProvider,
    InMemoryChunkRepository,
    InMemoryIngestionJobRepository,
    InMemoryProgressPublisher,
)
from packages.infrastructure.logging import configure_logging
from packages.infrastructure.memory import MemoryUnitOfWork
from packages.infrastructure.readiness import create_readiness_probes
from packages.infrastructure.search import HttpCrawlProvider, SearXNGProvider, SystemDNSResolver
from packages.infrastructure.settings import Settings, get_settings

logger = structlog.get_logger(__name__)


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Attach a caller-provided or generated trace ID to each HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = request.headers.get("X-Trace-ID") or str(uuid4())
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()


def create_app(
    settings: Settings | None = None,
    probes: dict[str, ReadinessProbe] | None = None,
) -> FastAPI:
    """Create the API with injected dependencies to keep health checks testable."""

    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)
    readiness_probes = probes if probes is not None else create_readiness_probes(runtime_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(
        title="AI Course Research Platform",
        version="0.1.0",
        description="Foundation API for the AI Research & Assessment Platform.",
        lifespan=lifespan,
    )
    app.add_middleware(TraceIdMiddleware)

    @app.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def ready() -> Response:
        unavailable: list[str] = []
        for name, probe in readiness_probes.items():
            try:
                await probe.ping()
            except Exception:
                unavailable.append(name)
                logger.warning("dependency_unavailable", dependency=name)

        if unavailable:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "unavailable": unavailable},
            )
        return JSONResponse(content={"status": "ok"})

    return app


app = create_app()

# Phase 2 routes intentionally delegate all persistence through application use cases.


class WorkspaceIn(BaseModel):
    name: str = Field(min_length=1)


class ProjectIn(BaseModel):
    workspace_id: UUID
    title: str
    description: str = ""
    domain: str
    target: str
    locale: str = "en"
    research_depth: int = Field(ge=1, le=10)
    created_by: UUID


class ProjectPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    actor_id: UUID


class SourceIn(BaseModel):
    source_type: str
    title: str
    canonical_url: str | None = None
    actor_id: UUID
    workspace_id: UUID


class SnapshotIn(BaseModel):
    snapshot_version: int = Field(ge=1)
    raw_content_reference: str | None = None
    content_hash: str
    metadata_json: dict[str, Any] = {}
    actor_id: UUID
    workspace_id: UUID


class CourseIn(BaseModel):
    title: str
    description: str = ""
    actor_id: UUID
    workspace_id: UUID


class VersionIn(BaseModel):
    version_number: int = Field(ge=1)
    title: str
    description: str = ""
    content_json: dict[str, Any] = {}
    created_by: UUID
    workspace_id: UUID
    parent_version_id: UUID | None = None


class VersionPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    content_json: dict[str, Any] | None = None
    actor_id: UUID
    workspace_id: UUID


class TextIngestionIn(BaseModel):
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_type: str = "TEXT"
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UrlIngestionIn(BaseModel):
    url: str
    title: str | None = None
    source_type: str = "URL"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchQueryIn(BaseModel):
    query_text: str = Field(min_length=1)
    query_family: QueryFamily = QueryFamily.DIRECT
    language: str | None = None
    locale: str | None = None
    domains_allowlist: tuple[str, ...] = ()
    domains_denylist: tuple[str, ...] = ()
    file_types: tuple[str, ...] = ()
    max_results: int = Field(default=10, ge=1, le=100)


class SearchQueryBatchIn(BaseModel):
    queries: list[SearchQueryIn] = Field(min_length=1, max_length=100)


class SearchResultAcceptIn(BaseModel):
    workspace_id: UUID
    actor_id: UUID
    title: str | None = None


class FetchRequestIn(BaseModel):
    url: str | None = None


def _phase2_routes(app: FastAPI) -> None:
    memory_uow = MemoryUnitOfWork()
    service = DomainService(lambda: memory_uow)
    app.state.memory_uow = memory_uow
    app.state.domain_service = service
    chunk_repository = InMemoryChunkRepository()
    job_repository = InMemoryIngestionJobRepository()
    progress_publisher = InMemoryProgressPublisher()
    ingestion = IngestionService(
        job_repository,
        chunk_repository,
        TextDocumentParser(),
        DeterministicEmbeddingProvider(),
        progress_publisher,
    )

    def trace(request: Request) -> str:
        return request.headers.get("X-Trace-ID", "")

    def error_handler(code: str, exc: Exception, request: Request) -> JSONResponse:
        return JSONResponse(
            status_code=404 if code == "NOT_FOUND" else 409,
            content={
                "error": {
                    "code": code,
                    "message": str(exc),
                    "details": {},
                    "trace_id": trace(request),
                }
            },
        )

    @app.exception_handler(NotFoundError)
    async def not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return error_handler("NOT_FOUND", exc, request)

    @app.exception_handler(ConflictError)
    async def conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return error_handler("CONFLICT", exc, request)

    @app.exception_handler(IngestionError)
    async def ingestion_error(request: Request, exc: IngestionError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": exc.code,
                    "message": str(exc),
                    "details": {},
                    "trace_id": trace(request),
                }
            },
        )

    @app.post("/api/v1/workspaces", status_code=201)
    async def create_workspace(body: WorkspaceIn, request: Request) -> Workspace:
        return await service.create_workspace(body.name, UUID(int=0), trace(request))

    @app.get("/api/v1/workspaces/{workspace_id}")
    async def get_workspace(workspace_id: UUID) -> Workspace:
        async with memory_uow as u:
            e = await u.workspaces.get(workspace_id)
            if not e:
                raise NotFoundError("Workspace not found")
            return e

    @app.post("/api/v1/projects", status_code=201)
    async def create_project(body: ProjectIn, request: Request) -> ResearchProject:
        return await service.create_project(ResearchProject(**body.model_dump()), trace(request))

    @app.get("/api/v1/projects/{project_id}")
    async def get_project(project_id: UUID) -> ResearchProject:
        return await service.get_project(project_id)

    @app.patch("/api/v1/projects/{project_id}")
    async def patch_project(
        project_id: UUID, body: ProjectPatch, request: Request
    ) -> ResearchProject:
        return await service.update_project(
            project_id,
            body.actor_id,
            trace(request),
            **body.model_dump(exclude={"actor_id"}, exclude_none=True),
        )

    @app.post("/api/v1/projects/{project_id}/sources", status_code=201)
    async def create_source(project_id: UUID, body: SourceIn, request: Request) -> Source:
        return await service.create_source(
            Source(project_id=project_id, **body.model_dump(exclude={"actor_id", "workspace_id"})),
            body.workspace_id,
            body.actor_id,
            trace(request),
        )

    @app.post("/api/v1/projects/{project_id}/sources/text", status_code=202)
    async def ingest_text(
        project_id: UUID, body: TextIngestionIn, request: Request
    ) -> dict[str, Any]:
        key = request.headers.get("Idempotency-Key")
        if not key:
            raise IngestionError("IDEMPOTENCY_CONFLICT", "Idempotency-Key is required")
        source, snapshot, job = await ingestion.ingest_text(
            project_id, body.title, body.text, key, trace(request), body.language
        )
        return {"source": source, "source_snapshot": snapshot, "ingestion_job": job}

    @app.post("/api/v1/projects/{project_id}/sources/url", status_code=202)
    async def register_url(
        project_id: UUID, body: UrlIngestionIn, request: Request
    ) -> dict[str, Any]:
        key = request.headers.get("Idempotency-Key")
        if not key:
            raise IngestionError("IDEMPOTENCY_CONFLICT", "Idempotency-Key is required")
        source, job = await ingestion.register_url(
            project_id, body.url, body.title, key, trace(request)
        )
        return {"source": source, "ingestion_job": job}

    @app.get("/api/v1/ingestion-jobs/{job_id}")
    async def get_ingestion_job(job_id: UUID) -> Any:
        job = await job_repository.get(job_id)
        if not job:
            raise NotFoundError("Ingestion job not found")
        return job

    @app.get("/api/v1/ingestion-jobs/{job_id}/events")
    async def get_ingestion_events(job_id: UUID) -> list[dict[str, object]]:
        return progress_publisher.events.get(job_id, [])

    @app.get("/api/v1/sources/{source_id}/snapshots/{snapshot_id}/chunks")
    async def get_snapshot_chunks(source_id: UUID, snapshot_id: UUID) -> list[Any]:
        return await chunk_repository.list_by_snapshot(snapshot_id)

    @app.get("/api/v1/projects/{project_id}/sources")
    async def list_sources(project_id: UUID) -> list[Source]:
        return await service.list_sources(project_id)

    @app.get("/api/v1/sources/{source_id}")
    async def get_source(source_id: UUID) -> Source:
        async with memory_uow as u:
            e = await u.sources.get(source_id)
            if not e:
                raise NotFoundError("Source not found")
            return e

    @app.post("/api/v1/sources/{source_id}/snapshots", status_code=201)
    async def create_snapshot(
        source_id: UUID, body: SnapshotIn, request: Request
    ) -> SourceSnapshot:
        return await service.create_snapshot(
            SourceSnapshot(
                source_id=source_id, **body.model_dump(exclude={"actor_id", "workspace_id"})
            ),
            body.workspace_id,
            body.actor_id,
            trace(request),
        )

    @app.get("/api/v1/sources/{source_id}/snapshots")
    async def list_snapshots(source_id: UUID) -> list[SourceSnapshot]:
        async with memory_uow as u:
            return await u.snapshots.list_for_source(source_id)

    @app.post("/api/v1/projects/{project_id}/courses", status_code=201)
    async def create_course(project_id: UUID, body: CourseIn, request: Request) -> Course:
        return await service.create_course(
            Course(project_id=project_id, title=body.title, description=body.description),
            body.workspace_id,
            body.actor_id,
            trace(request),
        )

    @app.get("/api/v1/courses/{course_id}")
    async def get_course(course_id: UUID) -> Course:
        async with memory_uow as u:
            e = await u.courses.get(course_id)
            if not e:
                raise NotFoundError("Course not found")
            return e

    @app.get("/api/v1/courses/{course_id}/versions")
    async def list_versions(course_id: UUID) -> list[CourseVersion]:
        async with memory_uow as u:
            return await u.course_versions.list_for_course(course_id)

    @app.get("/api/v1/courses/{course_id}/versions/{version_id}")
    async def get_version(course_id: UUID, version_id: UUID) -> CourseVersion:
        async with memory_uow as u:
            e = await u.course_versions.get(version_id)
            if not e or e.course_id != course_id:
                raise NotFoundError("Course version not found")
            return e

    @app.post("/api/v1/courses/{course_id}/versions", status_code=201)
    async def create_version(course_id: UUID, body: VersionIn, request: Request) -> CourseVersion:
        return await service.create_course_version(
            CourseVersion(course_id=course_id, **body.model_dump(exclude={"workspace_id"})),
            body.workspace_id,
            body.created_by,
            trace(request),
        )

    @app.patch("/api/v1/courses/{course_id}/versions/{version_id}")
    async def edit_version(
        course_id: UUID, version_id: UUID, body: VersionPatch, request: Request
    ) -> CourseVersion:
        return await service.edit_course_version(
            version_id,
            body.workspace_id,
            body.actor_id,
            trace(request),
            **body.model_dump(exclude={"workspace_id", "actor_id"}, exclude_none=True),
        )

    @app.post("/api/v1/courses/{course_id}/versions/{version_id}/publish")
    async def publish_version(
        course_id: UUID, version_id: UUID, body: CourseIn, request: Request
    ) -> CourseVersion:
        return await service.publish_course_version(
            version_id, body.workspace_id, body.actor_id, trace(request)
        )


_phase2_routes(app)


def _phase4_routes(app: FastAPI, settings: Settings) -> None:
    """Register Phase 4 endpoints over the same in-process boundary as Phase 2."""
    repository = InMemorySearchRepository()
    search = SearchService(repository, [SearXNGProvider(settings.searxng_url)])
    fetch_jobs: dict[UUID, FetchJob] = {}
    fetch_events: dict[UUID, list[dict[str, object]]] = {}
    crawler = HttpCrawlProvider(SystemDNSResolver())
    app.state.fetch_crawler = crawler

    def record(job: FetchJob) -> None:
        fetch_events[job.id].append(
            {
                "stage": job.stage,
                "status": job.status,
                "error_code": job.error_code,
            }
        )

    async def run_fetch(job_id: UUID) -> None:
        """Execute an accepted fetch and persist its resulting immutable snapshot."""
        job = fetch_jobs[job_id]
        job.status, job.stage, job.started_at = (
            FetchStatus.RUNNING,
            FetchStage.FETCHING,
            datetime.now(UTC),
        )
        record(job)
        try:
            document = await app.state.fetch_crawler.crawl_page(job.requested_url)
            async with app.state.memory_uow as uow:
                snapshots = await uow.snapshots.list_for_source(job.source_id)
                snapshot = SourceSnapshot(
                    job.source_id,
                    len(snapshots) + 1,
                    None,
                    document.raw_content_hash,
                    {
                        "canonical_url": document.canonical_url,
                        "final_url": document.final_url,
                        "normalized_content_hash": document.normalized_content_hash,
                        "normalized_markdown": document.normalized_markdown,
                    },
                )
                await uow.snapshots.add(snapshot)
            job.canonical_url = document.canonical_url
            job.final_url = document.final_url
            job.content_type = str(document.http_metadata.get("content_type", "text/html"))
            job.status, job.stage, job.completed_at = (
                FetchStatus.COMPLETED,
                FetchStage.COMPLETED,
                datetime.now(UTC),
            )
        except SearchError as exc:
            job.status, job.error_code, job.error_message, job.failed_at = (
                FetchStatus.BLOCKED if exc.code == "ROBOTS_DISALLOWED" else FetchStatus.FAILED,
                exc.code,
                str(exc),
                datetime.now(UTC),
            )
        except Exception:
            logger.exception("fetch_job_failed", fetch_job_id=str(job.id))
            job.status, job.error_code, job.error_message, job.failed_at = (
                FetchStatus.FAILED,
                "FETCH_FAILED",
                "Fetch worker failed",
                datetime.now(UTC),
            )
        record(job)

    def trace(request: Request) -> str:
        return request.headers.get("X-Trace-ID", "")

    @app.exception_handler(SearchError)
    async def search_error(request: Request, exc: SearchError) -> JSONResponse:
        return JSONResponse(
            status_code=404 if exc.code == "SEARCH_RESULT_NOT_FOUND" else 422,
            content={
                "error": {
                    "code": exc.code,
                    "message": str(exc),
                    "details": {},
                    "trace_id": trace(request),
                }
            },
        )

    @app.post("/api/v1/projects/{project_id}/search-queries", status_code=201)
    async def create_search_query(project_id: UUID, body: SearchQueryIn) -> SearchQuery:
        return await search.register(SearchQuery(project_id=project_id, **body.model_dump()))

    @app.post("/api/v1/projects/{project_id}/search-queries/batch", status_code=201)
    async def create_search_queries(
        project_id: UUID, body: SearchQueryBatchIn
    ) -> list[SearchQuery]:
        return [
            await search.register(SearchQuery(project_id=project_id, **query.model_dump()))
            for query in body.queries
        ]

    @app.post("/api/v1/search-queries/{query_id}/execute")
    async def execute_search_query(query_id: UUID, request: Request) -> list[Any]:
        key = request.headers.get("Idempotency-Key")
        if not key:
            raise SearchError("IDEMPOTENCY_CONFLICT", "Idempotency-Key is required")
        return await search.execute(query_id, key)

    @app.get("/api/v1/projects/{project_id}/search-queries")
    async def list_search_queries(project_id: UUID) -> list[SearchQuery]:
        return [query for query in repository.queries.values() if query.project_id == project_id]

    @app.get("/api/v1/search-queries/{query_id}")
    async def get_search_query(query_id: UUID) -> SearchQuery:
        query = repository.queries.get(query_id)
        if not query:
            raise SearchError("SEARCH_RESULT_NOT_FOUND", "Search query not found")
        return query

    @app.get("/api/v1/search-queries/{query_id}/results")
    async def get_search_results(query_id: UUID) -> list[Any]:
        if query_id not in repository.queries:
            raise SearchError("SEARCH_RESULT_NOT_FOUND", "Search query not found")
        return repository.results.get(query_id, [])

    @app.post("/api/v1/search-results/{result_id}/accept", status_code=201)
    async def accept_search_result(
        result_id: UUID, body: SearchResultAcceptIn, request: Request
    ) -> Source:
        result = next(
            (
                item
                for values in repository.results.values()
                for item in values
                if item.id == result_id
            ),
            None,
        )
        if not result:
            raise SearchError("SEARCH_RESULT_NOT_FOUND", "Search result not found")
        query = repository.queries[result.query_id]
        return await app.state.domain_service.create_source(
            Source(query.project_id, "WEB", body.title or result.title, result.canonical_url),
            body.workspace_id,
            body.actor_id,
            trace(request),
        )

    @app.post("/api/v1/sources/{source_id}/fetch", status_code=202)
    async def request_fetch(source_id: UUID, body: FetchRequestIn, request: Request) -> FetchJob:
        key = request.headers.get("Idempotency-Key")
        if not key:
            raise SearchError("IDEMPOTENCY_CONFLICT", "Idempotency-Key is required")
        async with app.state.memory_uow as uow:
            source = await uow.sources.get(source_id)
        if not source:
            raise NotFoundError("Source not found")
        url = body.url or source.canonical_url
        if not url:
            raise SearchError("SEARCH_QUERY_INVALID", "A source URL is required")
        existing = next((job for job in fetch_jobs.values() if job.idempotency_key == key), None)
        if existing:
            if existing.source_id != source_id or existing.requested_url != url:
                raise SearchError("IDEMPOTENCY_CONFLICT", "Idempotency key payload differs")
            return existing
        job = FetchJob(source.project_id, source_id, url, url, key, trace(request))
        fetch_jobs[job.id] = job
        fetch_events[job.id] = [{"stage": job.stage, "status": job.status}]
        asyncio.create_task(run_fetch(job.id))
        return job

    @app.get("/api/v1/fetch-jobs/{job_id}")
    async def get_fetch_job(job_id: UUID) -> FetchJob:
        job = fetch_jobs.get(job_id)
        if not job:
            raise NotFoundError("Fetch job not found")
        return job

    @app.get("/api/v1/fetch-jobs/{job_id}/events")
    async def get_fetch_events(job_id: UUID) -> list[dict[str, object]]:
        if job_id not in fetch_jobs:
            raise NotFoundError("Fetch job not found")
        return fetch_events[job_id]

    @app.get("/api/v1/snapshots/{snapshot_id}")
    async def get_snapshot(snapshot_id: UUID) -> SourceSnapshot:
        async with app.state.memory_uow as uow:
            snapshot = await uow.snapshots.get(snapshot_id)
        if not snapshot:
            raise NotFoundError("Source snapshot not found")
        return snapshot


_phase4_routes(app, get_settings())
