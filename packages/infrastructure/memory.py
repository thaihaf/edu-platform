from __future__ import annotations

from typing import Any


class MemoryRepository:
    def __init__(self, key: str = "id"):
        self.items: dict[Any, Any] = {}
        self.key = key

    async def add(self, e: Any) -> None:
        if e.id in self.items:
            raise ValueError("duplicate entity")
        if self.key != "id" and any(
            getattr(x, self.key) == getattr(e, self.key) for x in self.items.values()
        ):
            raise ValueError("duplicate constraint")
        self.items[e.id] = e

    async def get(self, i: Any) -> Any | None:
        return self.items.get(i)

    async def update(self, e: Any) -> None:
        self.items[e.id] = e

    async def update_draft(self, e: Any) -> None:
        self.items[e.id] = e

    async def list_for_project(self, i: Any) -> list[Any]:
        return [e for e in self.items.values() if e.project_id == i]

    async def list_for_source(self, i: Any) -> list[Any]:
        return [e for e in self.items.values() if e.source_id == i]

    async def list_for_course(self, i: Any) -> list[Any]:
        return [e for e in self.items.values() if e.course_id == i]

    async def append(self, e: Any) -> None:
        await self.add(e)


class MemoryUnitOfWork:
    def __init__(self):
        self.workspaces = MemoryRepository()
        self.projects = MemoryRepository()
        self.sources = MemoryRepository()
        self.snapshots = MemoryRepository("snapshot_version")
        self.courses = MemoryRepository()
        self.course_versions = MemoryRepository("version_number")
        self.audit_events = MemoryRepository()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False
