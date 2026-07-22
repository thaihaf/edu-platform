from __future__ import annotations

import asyncio
from uuid import uuid4

import httpx

from apps.api.app import main
from packages.domain.research import ObservationType, ResearchJob, ResearchObservation


def test_build_evidence_action_reads_job_observations_and_rejects_unknown_job() -> None:
    async def run() -> None:
        project_id = uuid4()
        job = ResearchJob(project_id, uuid4(), f"research-{uuid4()}", "test-trace")
        await main._research_jobs.save(job)
        await main._research_workflow.artifacts.save(
            job.id,
            "observation",
            ResearchObservation(
                project_id,
                job.id,
                uuid4(),
                uuid4(),
                ObservationType.CLAIM_CANDIDATE,
                "Research observations produce an evidence claim.",
            ),
        )
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                f"/api/v1/research-jobs/{job.id}/build-evidence",
                headers={"Idempotency-Key": f"evidence-{uuid4()}"},
            )
            missing = await client.post(
                f"/api/v1/research-jobs/{uuid4()}/build-evidence",
                headers={"Idempotency-Key": f"evidence-{uuid4()}"},
            )

        assert response.status_code == 200
        assert response.json()["claims_created"] == 1
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "RESEARCH_JOB_NOT_FOUND"

    asyncio.run(run())
