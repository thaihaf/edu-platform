"""Framework-independent Phase 2 domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class SourceType(StrEnum):
    URL = "URL"
    DOCUMENT = "DOCUMENT"
    PASTED_TEXT = "PASTED_TEXT"


class CourseVersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


@dataclass(frozen=True, slots=True)
class ResearchProject:
    id: UUID
    workspace_id: UUID
    title: str
    description: str | None
    domain: str
    target: str
    locale: str
    status: ProjectStatus
    research_depth: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: UUID,
        title: str,
        domain: str,
        target: str,
        created_by: UUID,
        description: str | None = None,
        locale: str = "en",
        research_depth: int = 1,
    ) -> "ResearchProject":
        if not title.strip() or research_depth < 1:
            raise ValueError("title and positive research_depth are required")
        now = utc_now()
        return cls(
            uuid4(),
            workspace_id,
            title,
            description,
            domain,
            target,
            locale,
            ProjectStatus.DRAFT,
            research_depth,
            created_by,
            now,
            now,
        )


@dataclass(frozen=True, slots=True)
class Source:
    id: UUID
    project_id: UUID
    canonical_url: str | None
    source_type: SourceType
    title: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: UUID,
        source_type: SourceType,
        canonical_url: str | None = None,
        title: str | None = None,
    ) -> "Source":
        if source_type is SourceType.URL and not canonical_url:
            raise ValueError("URL sources require canonical_url")
        now = utc_now()
        return cls(uuid4(), project_id, canonical_url, source_type, title, now, now)


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """An immutable, content-addressed source fetch result."""

    id: UUID
    source_id: UUID
    content: bytes
    content_hash: str
    fetched_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        source_id: UUID,
        content: bytes,
        content_hash: str,
        metadata: dict[str, Any] | None = None,
    ) -> "SourceSnapshot":
        if not content_hash:
            raise ValueError("content_hash is required")
        return cls(uuid4(), source_id, content, content_hash, utc_now(), metadata or {})


@dataclass(frozen=True, slots=True)
class Course:
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, *, project_id: UUID, title: str, description: str | None = None) -> "Course":
        if not title.strip():
            raise ValueError("title is required")
        now = utc_now()
        return cls(uuid4(), project_id, title, description, now, now)


@dataclass(frozen=True, slots=True)
class CourseVersion:
    id: UUID
    course_id: UUID
    version_number: int
    status: CourseVersionStatus
    content: dict[str, Any]
    created_at: datetime
    published_at: datetime | None = None

    @classmethod
    def draft(
        cls, *, course_id: UUID, version_number: int, content: dict[str, Any]
    ) -> "CourseVersion":
        if version_number < 1:
            raise ValueError("version_number must be positive")
        return cls(
            uuid4(), course_id, version_number, CourseVersionStatus.DRAFT, content, utc_now()
        )

    def edit(self, content: dict[str, Any]) -> "CourseVersion":
        if self.status is CourseVersionStatus.PUBLISHED:
            raise ValueError("published course versions are immutable")
        return CourseVersion(
            self.id,
            self.course_id,
            self.version_number,
            self.status,
            content,
            self.created_at,
            self.published_at,
        )

    def publish(self) -> "CourseVersion":
        if self.status is CourseVersionStatus.PUBLISHED:
            return self
        return CourseVersion(
            self.id,
            self.course_id,
            self.version_number,
            CourseVersionStatus.PUBLISHED,
            self.content,
            self.created_at,
            utc_now(),
        )


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    actor_id: UUID | None
    occurred_at: datetime
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def record(
        cls,
        *,
        entity_type: str,
        entity_id: UUID,
        action: str,
        actor_id: UUID | None = None,
        details: dict[str, Any] | None = None,
    ) -> "AuditEvent":
        return cls(uuid4(), entity_type, entity_id, action, actor_id, utc_now(), details or {})
