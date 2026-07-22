"""SQLAlchemy 2 async database setup and persistence models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON, TypeDecorator


class UUIDType(TypeDecorator[UUID]):
    """UUID storage compatible with PostgreSQL and isolated SQLite tests."""

    impl = PG_UUID(as_uuid=True)
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(36))
        return dialect.type_descriptor(PG_UUID(as_uuid=True))

    def process_bind_param(self, value: UUID | None, dialect: Any) -> UUID | str | None:
        return str(value) if value is not None and dialect.name == "sqlite" else value

    def process_result_value(self, value: UUID | None, dialect: Any) -> UUID | None:
        return UUID(value) if isinstance(value, str) and dialect.name == "sqlite" else value


class JSONType(TypeDecorator[dict[str, Any]]):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        return dialect.type_descriptor(JSON() if dialect.name == "sqlite" else JSONB())


class Base(DeclarativeBase):
    pass


class ProjectRecord(Base):
    __tablename__ = "research_projects"
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    locale: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    research_depth: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[UUID] = mapped_column(UUIDType(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceRecord(Base):
    __tablename__ = "sources"
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_projects.id"), nullable=False, index=True
    )
    canonical_url: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceSnapshotRecord(Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (
        UniqueConstraint("source_id", "content_hash", name="uq_source_snapshot_hash"),
    )
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"), nullable=False, index=True)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType(), nullable=False, default=dict)


class CourseRecord(Base):
    __tablename__ = "courses"
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_projects.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CourseVersionRecord(Base):
    __tablename__ = "course_versions"
    __table_args__ = (
        UniqueConstraint("course_id", "version_number", name="uq_course_version_number"),
    )
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSONType(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEventRecord(Base):
    __tablename__ = "audit_events"
    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(UUIDType(), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(UUIDType())
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONType(), nullable=False, default=dict)


def create_engine_and_sessionmaker(
    database_url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False)
