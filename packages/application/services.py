from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import Any
from uuid import UUID

from packages.domain.models import (
    AuditEvent,
    Course,
    CourseVersion,
    DomainError,
    ResearchProject,
    Source,
    SourceSnapshot,
    Workspace,
)
from packages.domain.ports import UnitOfWork


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class DomainService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self.uow_factory = uow_factory

    async def _mutate(
        self,
        action: str,
        workspace_id: UUID,
        actor_id: UUID,
        trace_id: str,
        entity_type: str,
        operation: Callable[[UnitOfWork], Awaitable[Any]],
    ) -> Any:
        async with self.uow_factory() as uow:
            try:
                entity = await operation(uow)
                await uow.audit_events.append(
                    AuditEvent(
                        workspace_id,
                        actor_id,
                        entity_type,
                        entity.id,
                        action,
                        trace_id,
                        new_values=asdict(entity),
                    )
                )
                await uow.commit()
                return entity
            except Exception:
                await uow.rollback()
                raise

    async def create_workspace(self, name: str, actor_id: UUID, trace_id: str) -> Workspace:
        w = Workspace(name)
        return await self._mutate(
            "workspace.created",
            w.id,
            actor_id,
            trace_id,
            "workspace",
            lambda u: self._add(u.workspaces, w),
        )

    async def _add(self, repo: Any, entity: Any) -> Any:
        await repo.add(entity)
        return entity

    async def create_project(self, entity: ResearchProject, trace_id: str) -> ResearchProject:
        return await self._mutate(
            "project.created",
            entity.workspace_id,
            entity.created_by,
            trace_id,
            "project",
            lambda u: self._add(u.projects, entity),
        )

    async def get_project(self, entity_id: UUID) -> ResearchProject:
        async with self.uow_factory() as u:
            e = await u.projects.get(entity_id)
            if not e:
                raise NotFoundError("Project not found")
            return e

    async def update_project(
        self, entity_id: UUID, actor: UUID, trace: str, **values: Any
    ) -> ResearchProject:
        async def op(u: UnitOfWork) -> ResearchProject:
            e = await u.projects.get(entity_id)
            if not e:
                raise NotFoundError("Project not found")
            try:
                e.update(**values)
            except DomainError as x:
                raise ConflictError(str(x)) from x
            await u.projects.update(e)
            return e

        return await self._mutate("project.updated", UUID(int=0), actor, trace, "project", op)

    async def create_source(
        self, entity: Source, workspace: UUID, actor: UUID, trace: str
    ) -> Source:
        return await self._mutate(
            "source.created",
            workspace,
            actor,
            trace,
            "source",
            lambda u: self._add(u.sources, entity),
        )

    async def list_sources(self, project: UUID) -> list[Source]:
        async with self.uow_factory() as u:
            return await u.sources.list_for_project(project)

    async def create_snapshot(
        self, entity: SourceSnapshot, workspace: UUID, actor: UUID, trace: str
    ) -> SourceSnapshot:
        return await self._mutate(
            "source_snapshot.created",
            workspace,
            actor,
            trace,
            "source_snapshot",
            lambda u: self._add(u.snapshots, entity),
        )

    async def create_course(
        self, entity: Course, workspace: UUID, actor: UUID, trace: str
    ) -> Course:
        return await self._mutate(
            "course.created",
            workspace,
            actor,
            trace,
            "course",
            lambda u: self._add(u.courses, entity),
        )

    async def create_course_version(
        self, entity: CourseVersion, workspace: UUID, actor: UUID, trace: str
    ) -> CourseVersion:
        return await self._mutate(
            "course_version.created",
            workspace,
            actor,
            trace,
            "course_version",
            lambda u: self._add(u.course_versions, entity),
        )

    async def edit_course_version(
        self, ident: UUID, workspace: UUID, actor: UUID, trace: str, **values: Any
    ) -> CourseVersion:
        async def op(u: UnitOfWork) -> CourseVersion:
            e = await u.course_versions.get(ident)
            if not e:
                raise NotFoundError("Course version not found")
            try:
                e.edit(**values)
            except DomainError as x:
                raise ConflictError(str(x)) from x
            await u.course_versions.update_draft(e)
            return e

        return await self._mutate(
            "course_version.edited", workspace, actor, trace, "course_version", op
        )

    async def publish_course_version(
        self, ident: UUID, workspace: UUID, actor: UUID, trace: str
    ) -> CourseVersion:
        async def op(u: UnitOfWork) -> CourseVersion:
            e = await u.course_versions.get(ident)
            if not e:
                raise NotFoundError("Course version not found")
            try:
                e.publish()
            except DomainError as x:
                raise ConflictError(str(x)) from x
            await u.course_versions.update_draft(e)
            return e

        return await self._mutate(
            "course_version.published", workspace, actor, trace, "course_version", op
        )
