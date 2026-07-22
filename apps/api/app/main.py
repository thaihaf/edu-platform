from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

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
from packages.infrastructure.logging import configure_logging
from packages.infrastructure.memory import MemoryUnitOfWork
from packages.infrastructure.readiness import create_readiness_probes
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


def _phase2_routes(app: FastAPI) -> None:
    memory_uow = MemoryUnitOfWork()
    service = DomainService(lambda: memory_uow)

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
