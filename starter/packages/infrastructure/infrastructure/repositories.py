"""SQLAlchemy implementations of the domain persistence ports."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import (
    AuditEvent,
    Course,
    CourseVersion,
    CourseVersionStatus,
    ProjectStatus,
    ResearchProject,
    Source,
    SourceSnapshot,
    SourceType,
)
from .database import (
    AuditEventRecord,
    CourseRecord,
    CourseVersionRecord,
    ProjectRecord,
    SourceRecord,
    SourceSnapshotRecord,
)


def _project(row: ProjectRecord) -> ResearchProject:
    return ResearchProject(
        row.id,
        row.workspace_id,
        row.title,
        row.description,
        row.domain,
        row.target,
        row.locale,
        ProjectStatus(row.status),
        row.research_depth,
        row.created_by,
        row.created_at,
        row.updated_at,
    )


def _source(row: SourceRecord) -> Source:
    return Source(
        row.id,
        row.project_id,
        row.canonical_url,
        SourceType(row.source_type),
        row.title,
        row.created_at,
        row.updated_at,
    )


def _course(row: CourseRecord) -> Course:
    return Course(
        row.id, row.project_id, row.title, row.description, row.created_at, row.updated_at
    )


def _version(row: CourseVersionRecord) -> CourseVersion:
    return CourseVersion(
        row.id,
        row.course_id,
        row.version_number,
        CourseVersionStatus(row.status),
        row.content_json,
        row.created_at,
        row.published_at,
    )


class SqlAlchemyProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, project: ResearchProject) -> None:
        self.session.add(
            ProjectRecord(
                id=project.id,
                workspace_id=project.workspace_id,
                title=project.title,
                description=project.description,
                domain=project.domain,
                target=project.target,
                locale=project.locale,
                status=project.status.value,
                research_depth=project.research_depth,
                created_by=project.created_by,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
        )

    async def get(self, project_id: UUID) -> ResearchProject | None:
        row = await self.session.get(ProjectRecord, project_id)
        return _project(row) if row else None

    async def list(self) -> list[ResearchProject]:
        return [_project(row) for row in (await self.session.scalars(select(ProjectRecord))).all()]

    async def update(self, project: ResearchProject) -> None:
        row = await self.session.get(ProjectRecord, project.id)
        if row is None:
            raise KeyError(project.id)
        for field in (
            "title",
            "description",
            "domain",
            "target",
            "locale",
            "status",
            "research_depth",
            "updated_at",
        ):
            value = getattr(project, field)
            setattr(row, field, value.value if field == "status" else value)


class SqlAlchemySourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, source: Source) -> None:
        self.session.add(
            SourceRecord(
                id=source.id,
                project_id=source.project_id,
                canonical_url=source.canonical_url,
                source_type=source.source_type.value,
                title=source.title,
                created_at=source.created_at,
                updated_at=source.updated_at,
            )
        )

    async def get(self, source_id: UUID) -> Source | None:
        row = await self.session.get(SourceRecord, source_id)
        return _source(row) if row else None

    async def list_for_project(self, project_id: UUID) -> list[Source]:
        rows = (
            await self.session.scalars(
                select(SourceRecord).where(SourceRecord.project_id == project_id)
            )
        ).all()
        return [_source(row) for row in rows]

    async def add_snapshot(self, snapshot: SourceSnapshot) -> None:
        self.session.add(
            SourceSnapshotRecord(
                id=snapshot.id,
                source_id=snapshot.source_id,
                content=snapshot.content,
                content_hash=snapshot.content_hash,
                fetched_at=snapshot.fetched_at,
                metadata_json=snapshot.metadata,
            )
        )

    async def list_snapshots(self, source_id: UUID) -> list[SourceSnapshot]:
        rows = (
            await self.session.scalars(
                select(SourceSnapshotRecord).where(SourceSnapshotRecord.source_id == source_id)
            )
        ).all()
        return [
            SourceSnapshot(
                row.id,
                row.source_id,
                row.content,
                row.content_hash,
                row.fetched_at,
                row.metadata_json,
            )
            for row in rows
        ]


class SqlAlchemyCourseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, course: Course) -> None:
        self.session.add(
            CourseRecord(
                id=course.id,
                project_id=course.project_id,
                title=course.title,
                description=course.description,
                created_at=course.created_at,
                updated_at=course.updated_at,
            )
        )

    async def get(self, course_id: UUID) -> Course | None:
        row = await self.session.get(CourseRecord, course_id)
        return _course(row) if row else None

    async def list_for_project(self, project_id: UUID) -> list[Course]:
        rows = (
            await self.session.scalars(
                select(CourseRecord).where(CourseRecord.project_id == project_id)
            )
        ).all()
        return [_course(row) for row in rows]

    async def add_version(self, version: CourseVersion) -> None:
        self.session.add(
            CourseVersionRecord(
                id=version.id,
                course_id=version.course_id,
                version_number=version.version_number,
                status=version.status.value,
                content_json=version.content,
                created_at=version.created_at,
                published_at=version.published_at,
            )
        )

    async def get_version(self, version_id: UUID) -> CourseVersion | None:
        row = await self.session.get(CourseVersionRecord, version_id)
        return _version(row) if row else None

    async def update_version(self, version: CourseVersion) -> None:
        row = await self.session.get(CourseVersionRecord, version.id)
        if row is None:
            raise KeyError(version.id)
        if row.status == CourseVersionStatus.PUBLISHED.value:
            raise ValueError("published course versions are immutable")
        row.status, row.content_json, row.published_at = (
            version.status.value,
            version.content,
            version.published_at,
        )

    async def next_version_number(self, course_id: UUID) -> int:
        maximum = await self.session.scalar(
            select(func.max(CourseVersionRecord.version_number)).where(
                CourseVersionRecord.course_id == course_id
            )
        )
        return (maximum or 0) + 1


class SqlAlchemyAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(self, event: AuditEvent) -> None:
        self.session.add(
            AuditEventRecord(
                id=event.id,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                action=event.action,
                actor_id=event.actor_id,
                occurred_at=event.occurred_at,
                details_json=event.details,
            )
        )
