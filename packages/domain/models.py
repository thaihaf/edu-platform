from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4


def utcnow() -> datetime:
    return datetime.now(UTC)


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class CourseVersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class DomainError(Exception):
    pass


class ImmutableResourceError(DomainError):
    pass


class InvalidStateTransitionError(DomainError):
    pass


class IngestionStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class IngestionStage(StrEnum):
    REGISTERING = "REGISTERING"
    STORING = "STORING"
    HASHING = "HASHING"
    PARSING = "PARSING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    PERSISTING = "PERSISTING"
    COMPLETED = "COMPLETED"


class InputType(StrEnum):
    TEXT = "TEXT"
    FILE = "FILE"
    URL = "URL"


@dataclass
class IngestionJob:
    project_id: UUID
    source_id: UUID
    source_snapshot_id: UUID | None
    input_type: InputType
    idempotency_key: str
    trace_id: str
    request_hash: str | None = None
    status: IngestionStatus = IngestionStatus.PENDING
    stage: IngestionStage = IngestionStage.REGISTERING
    progress_percent: int = 0
    retry_count: int = 0
    max_retries: int = 3
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def advance(self, stage: IngestionStage, progress_percent: int) -> None:
        order = list(IngestionStage)
        if self.status in {IngestionStatus.COMPLETED, IngestionStatus.CANCELLED}:
            raise InvalidStateTransitionError("Terminal ingestion job cannot advance")
        if order.index(stage) < order.index(self.stage):
            raise InvalidStateTransitionError("Ingestion stages cannot move backwards")
        self.status = IngestionStatus.RUNNING
        self.stage, self.progress_percent, self.started_at = (
            stage,
            progress_percent,
            self.started_at or utcnow(),
        )
        self.updated_at = utcnow()

    def complete(self) -> None:
        self.advance(IngestionStage.COMPLETED, 100)
        self.status, self.completed_at = IngestionStatus.COMPLETED, utcnow()

    def fail(self, code: str, message: str) -> None:
        if self.status is IngestionStatus.COMPLETED:
            raise InvalidStateTransitionError("Completed ingestion job cannot fail")
        self.status, self.error_code, self.error_message, self.failed_at = (
            IngestionStatus.FAILED,
            code,
            message,
            utcnow(),
        )
        self.updated_at = utcnow()


@dataclass(frozen=True)
class StructuredContentBlock:
    kind: str
    text: str = ""
    page_start: int | None = None
    page_end: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StructuredSection:
    heading: str | None
    heading_level: int | None
    section_path: tuple[str, ...]
    blocks: tuple[StructuredContentBlock, ...]
    page_start: int | None = None
    page_end: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StructuredDocument:
    title: str | None
    language: str | None
    source_mime_type: str
    parser_name: str
    parser_version: str
    sections: tuple[StructuredSection, ...]
    page_count: int | None = None
    parser_warnings: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceChunk:
    source_snapshot_id: UUID
    chunk_index: int
    text: str
    page_start: int | None
    page_end: int | None
    section_path: tuple[str, ...]
    heading: str | None
    token_count: int
    chunk_hash: str
    embedding: tuple[float, ...] | None = None
    embedding_model: str | None = None
    embedding_dimension: int | None = None
    metadata_json: Mapping[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Workspace:
    name: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class ResearchProject:
    workspace_id: UUID
    title: str
    description: str
    domain: str
    target: str
    locale: str
    research_depth: int
    created_by: UUID
    status: ProjectStatus = ProjectStatus.DRAFT
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def update(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        status: ProjectStatus | None = None,
    ) -> None:
        if self.status is ProjectStatus.ARCHIVED:
            raise ImmutableResourceError("Archived projects cannot be updated")
        if status and status not in {self.status, ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED}:
            raise InvalidStateTransitionError("Invalid project status transition")
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if status is not None:
            self.status = status
        self.updated_at = utcnow()


@dataclass
class Source:
    project_id: UUID
    source_type: str
    title: str
    canonical_url: str | None = None
    publisher: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime | None = None
    language: str | None = None
    access_status: str = "UNKNOWN"
    authority_score: float | None = None
    directness_score: float | None = None
    freshness_score: float | None = None
    commercial_bias_score: float | None = None
    independence_cluster_id: UUID | None = None
    content_hash: str | None = None
    metadata_json: Mapping[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class SourceSnapshot:
    source_id: UUID
    snapshot_version: int
    raw_content_reference: str | None
    content_hash: str
    metadata_json: Mapping[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    captured_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata_json", MappingProxyType(dict(self.metadata_json)))


@dataclass
class Course:
    project_id: UUID
    title: str
    description: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class CourseVersion:
    course_id: UUID
    version_number: int
    title: str
    description: str
    content_json: Mapping[str, Any]
    created_by: UUID
    status: CourseVersionStatus = CourseVersionStatus.DRAFT
    parent_version_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    published_at: datetime | None = None

    def edit(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        content_json: Mapping[str, Any] | None = None,
    ) -> None:
        if self.status is not CourseVersionStatus.DRAFT:
            raise ImmutableResourceError("Only draft course versions can be edited")
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if content_json is not None:
            self.content_json = dict(content_json)

    def publish(self) -> None:
        if self.status is not CourseVersionStatus.DRAFT:
            raise InvalidStateTransitionError("Only draft course versions can be published")
        self.status = CourseVersionStatus.PUBLISHED
        self.published_at = utcnow()


@dataclass(frozen=True)
class AuditEvent:
    workspace_id: UUID
    actor_id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    trace_id: str
    old_values: Mapping[str, Any] = field(default_factory=dict)
    new_values: Mapping[str, Any] = field(default_factory=dict)
    metadata_json: Mapping[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=utcnow)
