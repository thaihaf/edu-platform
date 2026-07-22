import asyncio
from uuid import uuid4

import pytest

from packages.application.research import ResearchService
from packages.domain.research import (
    ObservationType,
    ResearchError,
    ResearchJob,
    ResearchObservation,
    ResearchState,
    ResearchStatus,
)
from packages.infrastructure.research import (
    InMemoryResearchCheckpointStore,
    InMemoryResearchJobRepository,
    InMemoryResearchWorkflow,
)


def test_start_is_idempotent_and_queues_serializable_state() -> None:
    asyncio.run(_start_is_idempotent())


async def _start_is_idempotent() -> None:
    jobs = InMemoryResearchJobRepository()
    runner = InMemoryResearchWorkflow(jobs, InMemoryResearchCheckpointStore())
    service = ResearchService(jobs, runner)
    first = await service.start(uuid4(), uuid4(), " Learn Python ", "en", "key", "trace")
    again = await service.start(
        first.project_id, first.created_by, " Learn Python ", "en", "key", "trace"
    )
    assert first.id == again.id
    assert "user_goal" in (await runner.get_state(first.id)).serializable()
    with pytest.raises(ResearchError, match="different payload"):
        await service.start(first.project_id, first.created_by, "Different", "en", "key", "trace")


def test_cancel_preserves_checkpoint_and_prevents_resume() -> None:
    asyncio.run(_cancel_preserves_checkpoint())


async def _cancel_preserves_checkpoint() -> None:
    jobs = InMemoryResearchJobRepository()
    store = InMemoryResearchCheckpointStore()
    runner = InMemoryResearchWorkflow(jobs, store)
    job = ResearchJob(uuid4(), uuid4(), "key", "trace")
    await jobs.save(job)
    await runner.start(job, ResearchState(job.id, job.project_id, "goal", "en", {}))
    await runner.cancel(job.id)
    assert (await runner.get_progress(job.id)).status is ResearchStatus.CANCELLED
    assert await store.list_checkpoints(job.id) == ["queued"]
    with pytest.raises(ResearchError):
        await runner.resume(job.id)


def test_reported_question_requires_span() -> None:
    with pytest.raises(ResearchError):
        ResearchObservation(
            uuid4(), uuid4(), uuid4(), None, ObservationType.REPORTED_QUESTION_CANDIDATE, "q"
        )
