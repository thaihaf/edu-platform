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
