from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities import AuditEvent, Course, CourseVersion, ResearchProject, Source, SourceType
from infrastructure.database import create_engine_and_sessionmaker
from infrastructure.repositories import (
    SqlAlchemyAuditRepository,
    SqlAlchemyCourseRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemySourceRepository,
)


class ProjectCreate(BaseModel):
    workspace_id: UUID
    title: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=1)
    target: str = Field(min_length=1)
    created_by: UUID
    description: str | None = None
    locale: str = "en"
    research_depth: int = Field(default=1, ge=1)


class SourceCreate(BaseModel):
    source_type: SourceType
    canonical_url: str | None = None
    title: str | None = None


class CourseCreate(BaseModel):
    project_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class VersionCreate(BaseModel):
    content: dict[str, Any]


class VersionUpdate(BaseModel):
    content: dict[str, Any]


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def project_output(value: ResearchProject) -> dict[str, Any]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def source_output(value: Source) -> dict[str, Any]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def course_output(value: Course) -> dict[str, Any]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def version_output(value: CourseVersion) -> dict[str, Any]:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}


def create_app(session_factory: async_sessionmaker[AsyncSession] | None = None) -> FastAPI:
    if session_factory is None:
        _, session_factory = create_engine_and_sessionmaker(
            os.getenv(
                "DATABASE_URL", "postgresql+asyncpg://ai_course:ai_course@localhost:5432/ai_course"
            )
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        yield

    app = FastAPI(title="AI Course Research Platform", version="0.2.0", lifespan=lifespan)
    app.state.session_factory = session_factory

    async def session() -> AsyncGenerator[AsyncSession, None]:
        async with app.state.session_factory() as value:
            try:
                yield value
                await value.commit()
            except Exception:
                await value.rollback()
                raise

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/projects", status_code=status.HTTP_201_CREATED)
    async def create_project(
        payload: ProjectCreate, db: AsyncSession = Depends(session)
    ) -> dict[str, Any]:
        value = ResearchProject.create(**payload.model_dump())
        await SqlAlchemyProjectRepository(db).add(value)
        await SqlAlchemyAuditRepository(db).record(
            AuditEvent.record(
                entity_type="project",
                entity_id=value.id,
                action="created",
                actor_id=value.created_by,
            )
        )
        return project_output(value)

    @app.get("/projects")
    async def list_projects(db: AsyncSession = Depends(session)) -> list[dict[str, Any]]:
        return [project_output(value) for value in await SqlAlchemyProjectRepository(db).list()]

    @app.post("/projects/{project_id}/sources", status_code=status.HTTP_201_CREATED)
    async def create_source(
        project_id: UUID, payload: SourceCreate, db: AsyncSession = Depends(session)
    ) -> dict[str, Any]:
        if not await SqlAlchemyProjectRepository(db).get(project_id):
            raise HTTPException(404, "project not found")
        try:
            value = Source.create(project_id=project_id, **payload.model_dump())
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        await SqlAlchemySourceRepository(db).add(value)
        await SqlAlchemyAuditRepository(db).record(
            AuditEvent.record(entity_type="source", entity_id=value.id, action="created")
        )
        return source_output(value)

    @app.get("/projects/{project_id}/sources")
    async def list_sources(
        project_id: UUID, db: AsyncSession = Depends(session)
    ) -> list[dict[str, Any]]:
        return [
            source_output(value)
            for value in await SqlAlchemySourceRepository(db).list_for_project(project_id)
        ]

    @app.post("/courses", status_code=status.HTTP_201_CREATED)
    async def create_course(
        payload: CourseCreate, db: AsyncSession = Depends(session)
    ) -> dict[str, Any]:
        if not await SqlAlchemyProjectRepository(db).get(payload.project_id):
            raise HTTPException(404, "project not found")
        value = Course.create(**payload.model_dump())
        await SqlAlchemyCourseRepository(db).add(value)
        await SqlAlchemyAuditRepository(db).record(
            AuditEvent.record(entity_type="course", entity_id=value.id, action="created")
        )
        return course_output(value)

    @app.post("/courses/{course_id}/versions", status_code=status.HTTP_201_CREATED)
    async def create_version(
        course_id: UUID, payload: VersionCreate, db: AsyncSession = Depends(session)
    ) -> dict[str, Any]:
        repo = SqlAlchemyCourseRepository(db)
        if not await repo.get(course_id):
            raise HTTPException(404, "course not found")
        value = CourseVersion.draft(
            course_id=course_id,
            version_number=await repo.next_version_number(course_id),
            content=payload.content,
        )
        await repo.add_version(value)
        await SqlAlchemyAuditRepository(db).record(
            AuditEvent.record(entity_type="course_version", entity_id=value.id, action="created")
        )
        return version_output(value)

    @app.put("/course-versions/{version_id}")
    async def update_version(
        version_id: UUID, payload: VersionUpdate, db: AsyncSession = Depends(session)
    ) -> dict[str, Any]:
        repo = SqlAlchemyCourseRepository(db)
        current = await repo.get_version(version_id)
        if not current:
            raise HTTPException(404, "course version not found")
        try:
            value = current.edit(payload.content)
            await repo.update_version(value)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        await SqlAlchemyAuditRepository(db).record(
            AuditEvent.record(entity_type="course_version", entity_id=value.id, action="updated")
        )
        return version_output(value)

    @app.post("/course-versions/{version_id}/publish")
    async def publish_version(
        version_id: UUID, db: AsyncSession = Depends(session)
    ) -> dict[str, Any]:
        repo = SqlAlchemyCourseRepository(db)
        current = await repo.get_version(version_id)
        if not current:
            raise HTTPException(404, "course version not found")
        value = current.publish()
        await repo.update_version(value)
        await SqlAlchemyAuditRepository(db).record(
            AuditEvent.record(entity_type="course_version", entity_id=value.id, action="published")
        )
        return version_output(value)

    return app


app = create_app()
