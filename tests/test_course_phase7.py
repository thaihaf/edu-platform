import asyncio
from uuid import uuid4

import pytest

from packages.application.course import CourseService, fingerprint
from packages.domain.course import CourseError, CourseGenerationJob
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    ClaimType,
    EvidenceLink,
    EvidenceRelation,
    Skill,
    SkillType,
)
from packages.infrastructure.course import InMemoryCourseRepository


def fixtures():
    p = uuid4()
    claim = Claim(p, "Approved fact", ClaimType.DOMAIN_FACT, status=ClaimStatus.VERIFIED)
    link = EvidenceLink(p, claim.id, uuid4(), uuid4(), (), EvidenceRelation.SUPPORTS, 1, 1, None, 1)
    skill = Skill(p, "Python", "python", "", SkillType.TECHNOLOGY, status="APPROVED")
    return p, claim, link, skill


def test_generation_is_idempotent_cited_and_publishable():
    async def run():
        p, c, l, s = fixtures()
        r = InMemoryCourseRepository()
        service = CourseService(r, [c], [s], {c.id: [l]})
        j = CourseGenerationJob(
            p, "key", "Learn Python", "beginner", uuid4(), request_fingerprint=fingerprint({"x": 1})
        )
        assert await service.start(j) is j
        await service.generate(j.id)
        assert j.status == "COMPLETED"
        version = await r.version_for_job(j.id)
        assert not await service.validate(version.id)
        assert (await service.publish(version.id)).status == "PUBLISHED"
        copy = await service.copy_as_draft(version.id)
        assert copy.parent_version_id == version.id

    asyncio.run(run())


def test_rejects_unverified_evidence_and_idempotency_conflict():
    async def run():
        p, c, l, s = fixtures()
        c.status = ClaimStatus.REJECTED
        r = InMemoryCourseRepository()
        service = CourseService(r, [c], [s], {c.id: [l]})
        j = CourseGenerationJob(p, "key", "Learn", "a", uuid4(), request_fingerprint="a")
        await service.start(j)
        with pytest.raises(CourseError, match="verified"):
            await service.generate(j.id)
        with pytest.raises(CourseError):
            await service.start(
                CourseGenerationJob(p, "key", "Other", "a", uuid4(), request_fingerprint="b")
            )

    asyncio.run(run())
