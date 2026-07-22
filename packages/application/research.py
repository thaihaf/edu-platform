"""Research use cases and deterministic policies; no workflow-provider imports."""

from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import UUID

from packages.domain.research import (
    ResearchError,
    ResearchJob,
    ResearchJobRepository,
    ResearchState,
    ResearchWorkflow,
)


class ResearchService:
    def __init__(self, jobs: ResearchJobRepository, workflow: ResearchWorkflow):
        self.jobs, self.workflow = jobs, workflow

    async def start(
        self,
        project_id: UUID,
        created_by: UUID,
        goal: str,
        locale: str,
        key: str,
        trace_id: str,
        depth: int = 1,
        learner_context: str | None = None,
        time_range: str | None = None,
        policy: dict[str, Any] | None = None,
    ) -> ResearchJob:
        if not goal.strip():
            raise ResearchError("INVALID_RESEARCH_GOAL", "Goal is required")
        payload = (
            f"{project_id}|{goal.strip()}|{locale}|{depth}|{learner_context}|{time_range}|{policy}"
        )
        digest = sha256(payload.encode()).hexdigest()
        existing = await self.jobs.by_key(key)
        if existing:
            if existing.request_hash != digest:
                raise ResearchError(
                    "IDEMPOTENCY_CONFLICT", "Idempotency key was used with a different payload"
                )
            return existing
        job = ResearchJob(
            project_id=project_id,
            created_by=created_by,
            idempotency_key=key,
            trace_id=trace_id,
            research_depth=depth,
            request_hash=digest,
        )
        state = ResearchState(
            job.id,
            project_id,
            goal,
            locale,
            policy or {},
            learner_context,
            time_range,
            budgets=job.budgets,
        )
        await self.jobs.save(job)
        await self.workflow.start(job, state)
        return job

    async def get(self, id: UUID) -> ResearchJob:
        job = await self.jobs.get(id)
        if not job:
            raise ResearchError("RESEARCH_JOB_NOT_FOUND", "Research job not found")
        return job

    async def cancel(self, id: UUID) -> ResearchJob:
        await self.get(id)
        await self.workflow.cancel(id)
        return await self.get(id)

    async def resume(self, id: UUID) -> ResearchJob:
        await self.get(id)
        await self.workflow.resume(id)
        return await self.get(id)

    async def retry(self, id: UUID) -> ResearchJob:
        await self.get(id)
        await self.workflow.retry(id)
        return await self.get(id)
