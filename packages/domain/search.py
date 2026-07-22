"""Framework-neutral Phase 4 search and public-web fetching contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


def now() -> datetime:
    return datetime.now(UTC)


class QueryFamily(StrEnum):
    DIRECT = "DIRECT"
    CANDIDATE_LANGUAGE = "CANDIDATE_LANGUAGE"
    FILE_TYPE = "FILE_TYPE"
    SITE_SPECIFIC = "SITE_SPECIFIC"
    PHRASE_FINGERPRINT = "PHRASE_FINGERPRINT"
    TEMPORAL = "TEMPORAL"
    ENTITY_ALIAS = "ENTITY_ALIAS"
    CONTRADICTION = "CONTRADICTION"
    CITATION_CHASING = "CITATION_CHASING"
    RELATED_ORGANIZATION = "RELATED_ORGANIZATION"
    TECHNOLOGY_SPECIFIC = "TECHNOLOGY_SPECIFIC"
    DOMAIN_SPECIFIC = "DOMAIN_SPECIFIC"


class QueryStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FetchStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class FetchStage(StrEnum):
    VALIDATING = "VALIDATING"
    RESOLVING = "RESOLVING"
    ROBOTS_CHECK = "ROBOTS_CHECK"
    FETCHING = "FETCHING"
    REDIRECT_VALIDATION = "REDIRECT_VALIDATION"
    NORMALIZING = "NORMALIZING"
    SNAPSHOTTING = "SNAPSHOTTING"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class SearchOptions:
    locale: str | None = None
    language: str | None = None
    time_range: str | None = None
    domains_allowlist: tuple[str, ...] = ()
    domains_denylist: tuple[str, ...] = ()
    file_types: tuple[str, ...] = ()
    safe_search: bool = True
    result_limit: int = 10
    page: int = 1
    cursor: str | None = None


@dataclass(frozen=True)
class ProviderSearchResult:
    title: str
    url: str
    snippet: str = ""
    published_at: datetime | None = None
    content_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResultPage:
    results: tuple[ProviderSearchResult, ...]
    next_cursor: str | None = None


@dataclass
class SearchQuery:
    project_id: UUID
    query_text: str
    query_family: QueryFamily
    language: str | None = None
    locale: str | None = None
    time_from: datetime | None = None
    time_to: datetime | None = None
    domains_allowlist: tuple[str, ...] = ()
    domains_denylist: tuple[str, ...] = ()
    file_types: tuple[str, ...] = ()
    max_results: int = 10
    status: QueryStatus = QueryStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass
class SearchResult:
    query_id: UUID
    provider: str
    provider_rank: int
    normalized_rank: int
    title: str
    url: str
    canonical_url: str
    snippet: str
    published_at: datetime | None
    discovered_at: datetime
    content_type: str | None
    relevance_score: float
    source_type_guess: str
    access_status: str = "DISCOVERED"
    metadata_json: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)


@dataclass
class FetchJob:
    project_id: UUID
    source_id: UUID
    requested_url: str
    canonical_url: str
    idempotency_key: str
    trace_id: str
    status: FetchStatus = FetchStatus.PENDING
    stage: FetchStage = FetchStage.VALIDATING
    retry_count: int = 0
    max_retries: int = 3
    http_status: int | None = None
    content_type: str | None = None
    content_length: int | None = None
    final_url: str | None = None
    redirect_count: int = 0
    robots_decision: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class NormalizedWebDocument:
    requested_url: str
    final_url: str
    canonical_url: str
    title: str | None
    description: str | None
    author: str | None
    publisher: str | None
    published_at: datetime | None
    modified_at: datetime | None
    language: str | None
    visible_text: str
    normalized_markdown: str
    headings: tuple[str, ...]
    links: tuple[str, ...]
    canonical_link: str | None
    metadata: dict[str, Any]
    extraction_warnings: tuple[str, ...]
    raw_content_hash: str
    normalized_content_hash: str
    fetched_at: datetime
    http_metadata: dict[str, Any]


@dataclass(frozen=True)
class SourceQuality:
    authority: float
    directness: float
    freshness: float
    specificity: float
    commercial_bias: float
    completeness: float
    likely_independence: float
    accessibility: float
    relevance: float

    def aggregate(self, weights: dict[str, float] | None = None) -> float:
        values = self.__dict__
        weights = weights or {key: 1.0 for key in values}
        return float(
            sum(values[key] * weights.get(key, 0.0) for key in values)
            / sum(weights.get(key, 0.0) for key in values)
        )
