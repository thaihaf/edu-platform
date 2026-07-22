"""In-memory Phase 5 adapters and optional LangGraph production adapter boundary."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from packages.domain.research import (
    ResearchError,
    ResearchJob,
    ResearchPhase,
    ResearchState,
    ResearchStatus,
)


class InMemoryResearchJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[UUID, ResearchJob] = {}
        self.keys: dict[str, UUID] = {}

    async def get(self, id: UUID) -> ResearchJob | None:
        return self.jobs.get(id)

    async def by_key(self, key: str) -> ResearchJob | None:
        return self.jobs.get(self.keys[key]) if key in self.keys else None

    async def save(self, job: ResearchJob) -> ResearchJob:
        self.jobs[job.id] = job
        self.keys[job.idempotency_key] = job.id
        return job


class InMemoryResearchCheckpointStore:
    def __init__(self) -> None:
        self.states: dict[UUID, ResearchState] = {}
        self.nodes: dict[UUID, list[str]] = {}

    async def save_checkpoint(self, job_id: UUID, node: str, state: ResearchState) -> None:
        if state.workflow_version != "phase5.v1":
            raise ResearchError("RESEARCH_CHECKPOINT_INCOMPATIBLE", "Unsupported workflow version")
        self.states[job_id] = state
        self.nodes.setdefault(job_id, []).append(node)

    async def load_checkpoint(self, job_id: UUID, workflow_version: str) -> ResearchState:
        state = self.states.get(job_id)
        if not state:
            raise ResearchError("RESEARCH_CHECKPOINT_NOT_FOUND", "Checkpoint not found")
        if state.workflow_version != workflow_version:
            raise ResearchError(
                "RESEARCH_CHECKPOINT_INCOMPATIBLE", "Checkpoint workflow version differs"
            )
        return state

    async def list_checkpoints(self, job_id: UUID) -> list[str]:
        return self.nodes.get(job_id, [])

    async def mark_terminal(self, job_id: UUID) -> None:
        pass


class InMemoryResearchWorkflow:
    """Test runner: persists queued state only; workers explicitly resume it."""

    def __init__(
        self, jobs: InMemoryResearchJobRepository, checkpoints: InMemoryResearchCheckpointStore
    ):
        self.jobs, self.checkpoints = jobs, checkpoints

    async def start(self, job: ResearchJob, state: ResearchState) -> None:
        await self.checkpoints.save_checkpoint(job.id, "queued", state)

    async def get_state(self, job_id: UUID) -> ResearchState:
        return await self.checkpoints.load_checkpoint(job_id, "phase5.v1")

    async def get_progress(self, job_id: UUID) -> ResearchJob:
        job = await self.jobs.get(job_id)
        if not job:
            raise ResearchError("RESEARCH_JOB_NOT_FOUND", "Research job not found")
        return job

    async def cancel(self, job_id: UUID) -> None:
        job = await self.get_progress(job_id)
        job.cancellation_requested = True
        if job.status is not ResearchStatus.CANCELLED:
            job.transition(ResearchStatus.CANCELLED)
        await self.jobs.save(job)
        await self.checkpoints.mark_terminal(job_id)

    async def resume(self, job_id: UUID) -> None:
        job = await self.get_progress(job_id)
        if job.status is ResearchStatus.COMPLETED:
            raise ResearchError("RESEARCH_ALREADY_COMPLETED", "Completed research cannot resume")
        if job.status is ResearchStatus.CANCELLED:
            raise ResearchError("RESEARCH_CANCELLED", "Cancelled research cannot resume")
        if job.status is ResearchStatus.PENDING:
            job.transition(ResearchStatus.RUNNING)
        if job.status is ResearchStatus.PAUSED:
            job.transition(ResearchStatus.RUNNING)
        job.current_phase = ResearchPhase.SCOPING
        job.current_node = "understand_goal"
        await self.jobs.save(job)

    async def retry(self, job_id: UUID) -> None:
        job = await self.get_progress(job_id)
        if job.status is not ResearchStatus.FAILED:
            raise ResearchError("INVALID_RESEARCH_TRANSITION", "Only failed research can retry")
        if job.retry_count >= job.max_retries:
            raise ResearchError("RESEARCH_BUDGET_EXHAUSTED", "Retry budget exhausted")
        job.retry_count += 1
        job.transition(ResearchStatus.RUNNING)
        await self.jobs.save(job)


class LangGraphResearchWorkflow:
    """Production adapter requires LangGraph at runtime, never at import time."""

    def __init__(self, *_: Any, **__: Any) -> None:
        from importlib.util import find_spec

        if find_spec("langgraph") is None:
            raise ResearchError("WORKFLOW_PROVIDER_UNAVAILABLE", "LangGraph is not installed")
        from importlib import import_module

        self.langgraph = import_module("langgraph")
