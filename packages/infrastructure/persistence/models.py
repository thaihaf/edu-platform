from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    pass


class WorkspaceRow(Base):
    __tablename__ = "workspaces"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProjectRow(Base):
    __tablename__ = "research_projects"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(String)
    domain: Mapped[str] = mapped_column(String(255))
    target: Mapped[str] = mapped_column(String(500))
    locale: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    research_depth: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[UUID] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceRow(Base):
    __tablename__ = "sources"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    source_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(500))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceSnapshotRow(Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (
        UniqueConstraint("source_id", "snapshot_version", name="uq_snapshot_source_version"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"))
    snapshot_version: Mapped[int] = mapped_column(Integer)
    raw_content_reference: Mapped[str | None] = mapped_column(String)
    content_hash: Mapped[str] = mapped_column(String(128))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CourseRow(Base):
    __tablename__ = "courses"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("research_projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CourseVersionRow(Base):
    __tablename__ = "course_versions"
    __table_args__ = (
        UniqueConstraint("course_id", "version_number", name="uq_course_version_number"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(String)
    content_json: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[UUID] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    parent_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("course_versions.id"))


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    actor_id: Mapped[UUID] = mapped_column(Uuid)
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[UUID] = mapped_column(Uuid)
    action: Mapped[str] = mapped_column(String(100))
    old_values: Mapped[dict] = mapped_column(JSON, default=dict)
    new_values: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    trace_id: Mapped[str] = mapped_column(String(100))
