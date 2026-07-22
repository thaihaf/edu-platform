"""Deterministic Phase 7 course generation policies and use cases."""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from typing import Any
from uuid import UUID

from packages.domain.course import *
from packages.domain.evidence import ClaimStatus
from packages.domain.models import Course, CourseVersion, CourseVersionStatus


def fingerprint(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def clean_title(value: str) -> str:
    return " ".join(value.split()).strip()


def safe_content(value: dict[str, Any]) -> None:
    if "<script" in json.dumps(value).lower() or "javascript:" in json.dumps(value).lower():
        raise CourseError("COURSE_GENERATION_INPUT_INVALID", "Executable HTML is forbidden")


class EvidenceSelector:
    def select(
        self, claims: list[Any], skills: list[Any], links: dict[UUID, list[Any]]
    ) -> tuple[list[Any], list[Any], dict[str, str]]:
        selected = []
        reasons = {}
        for c in claims:
            if c.status in {ClaimStatus.VERIFIED, ClaimStatus.PROBABLE, ClaimStatus.DISPUTED}:
                selected.append(c)
                reasons[str(c.id)] = (
                    "contradiction note" if c.status is ClaimStatus.DISPUTED else "approved claim"
                )
            else:
                reasons[str(c.id)] = "excluded: unapproved claim"
        approved = [s for s in skills if getattr(s, "status", "") in {"APPROVED", "VERIFIED"}]
        for s in skills:
            reasons[str(s.id)] = "approved skill" if s in approved else "excluded: unapproved skill"
        return selected, approved, reasons


class DeterministicCurriculumPlanner:
    def plan(
        self, job: CourseGenerationJob, claims: list[Any], skills: list[Any]
    ) -> CurriculumPlan:
        if not any(c.status is ClaimStatus.VERIFIED for c in claims):
            raise CourseError(
                "INSUFFICIENT_VERIFIED_EVIDENCE", "At least one verified claim is required"
            )
        if not skills:
            raise CourseError(
                "INSUFFICIENT_SKILL_COVERAGE", "At least one approved skill is required"
            )
        modules = [
            {
                "title": clean_title(s.name),
                "skill_id": s.id,
                "lessons": [
                    {
                        "title": f"Apply {clean_title(s.name)}",
                        "objective": f"Apply {clean_title(s.name)}",
                    }
                ],
            }
            for s in sorted(skills, key=lambda x: x.normalized_name)
        ]
        if job.module_limit:
            modules = modules[: job.module_limit]
        return CurriculumPlan(
            job.project_id,
            job.id,
            clean_title(job.target_outcome),
            f"Course for {job.target_audience}",
            job.target_outcome,
            job.target_audience,
            modules,
            [s.id for s in skills],
            [c.id for c in claims if c.status is ClaimStatus.VERIFIED],
            ["Unresolved gaps remain review warnings."]
            if any(c.status is ClaimStatus.DISPUTED for c in claims)
            else [],
        )


class CourseService:
    def __init__(
        self, repository: Any, claims: list[Any], skills: list[Any], links: dict[UUID, list[Any]]
    ):
        self.r, self.claims, self.skills, self.links = repository, claims, skills, links
        self.selector = EvidenceSelector()
        self.planner = DeterministicCurriculumPlanner()

    async def start(self, job: CourseGenerationJob) -> CourseGenerationJob:
        old = await self.r.job_by_key(job.idempotency_key)
        if old:
            if old.request_fingerprint != job.request_fingerprint:
                raise CourseError("IDEMPOTENCY_CONFLICT", "Idempotency key payload differs")
            return old
        await self.r.add_job(job)
        return job

    async def generate(self, job_id: UUID) -> CourseGenerationJob:
        job = await self.r.get_job(job_id)
        if not job:
            raise CourseError("COURSE_GENERATION_JOB_NOT_FOUND", "Generation job not found")
        if job.status is GenerationStatus.COMPLETED:
            return job
        try:
            job.advance(GenerationStage.SELECTING_EVIDENCE, 15)
            chosen, skills, reasons = self.selector.select(self.claims, self.skills, self.links)
            await self.r.event(job, "evidence_selected", reasons)
            job.advance(GenerationStage.PLANNING_CURRICULUM, 30)
            course = await self.r.get_course(job.course_id) if job.course_id else None
            if job.course_id and not course:
                raise CourseError("COURSE_NOT_FOUND", "Requested course does not exist")
            if course and course.project_id != job.project_id:
                raise CourseError(
                    "COURSE_PROJECT_MISMATCH", "Requested course does not belong to this project"
                )
            plan = self.planner.plan(job, chosen, skills)
            await self.r.add_plan(plan)
            if not course:
                course = Course(job.project_id, plan.title, plan.description)
                await self.r.add_course(course)
                job.course_id = course.id
            version = await self.r.version_for_job(job.id)
            if not version:
                version = CourseVersion(
                    course.id,
                    len(await self.r.versions(course.id)) + 1,
                    plan.title,
                    plan.description,
                    {"generation_job_id": str(job.id)},
                    job.created_by,
                )
                await self.r.add_version(version, job.id)
            job.advance(GenerationStage.BUILDING_MODULES, 50)
            for position, m in enumerate(plan.module_plan, 1):
                module = await self.r.module_for(version.id, position)
                if not module:
                    module = Module(version.id, position, m["title"], (m["skill_id"],))
                    await self.r.add_module(module)
                job.advance(GenerationStage.BUILDING_LESSONS, 65)
                if not await self.r.lesson_for(module.id, 1):
                    claim = next(c for c in chosen if c.status is ClaimStatus.VERIFIED)
                    objective = LearningObjective(
                        m["lessons"][0]["objective"],
                        "Apply",
                        BloomLevel.APPLY,
                        (m["skill_id"],),
                        (claim.id,),
                    )
                    lesson = Lesson(
                        module.id,
                        1,
                        m["lessons"][0]["title"],
                        f"Practice {m['title']}",
                        (objective.id,),
                    )
                    await self.r.add_objective(objective, lesson.id)
                    await self.r.add_lesson(lesson)
                    evidence_links = self.links.get(claim.id, [])
                    if not evidence_links:
                        raise CourseError(
                            "MISSING_EVIDENCE_LINK",
                            "Verified claim is missing an evidence link",
                        )
                    link = evidence_links[0]
                    block = ContentBlock(
                        lesson.id,
                        1,
                        ContentBlockType.PARAGRAPH,
                        {"text": f"{m['title']} is grounded in approved evidence."},
                        ConfidenceClass.CONFIRMED,
                        (claim.id,),
                        (m["skill_id"],),
                        (link.id,),
                    )
                    safe_content(block.content_json)
                    await self.r.add_block(block)
                    await self.r.add_citation(
                        Citation(
                            job.project_id,
                            version.id,
                            claim.id,
                            link.id,
                            link.source_id,
                            link.source_snapshot_id,
                            block.id,
                        )
                    )
            job.advance(GenerationStage.VALIDATING_DRAFT, 85)
            errors = await self.validate(version.id)
            if errors:
                raise CourseError("COURSE_VERSION_VALIDATION_FAILED", "; ".join(errors))
            job.advance(GenerationStage.PERSISTING_VERSION, 95)
            job.complete()
            await self.r.event(job, "completed", {"course_version_id": str(version.id)})
            return job
        except CourseError as exc:
            job.fail(exc.code, exc.message)
            await self.r.event(job, "failed", {"code": exc.code})
            raise

    async def validate(self, version_id: UUID) -> list[str]:
        modules = await self.r.modules(version_id)
        errors = []
        if not modules:
            errors.append("at least one module required")
        for m in modules:
            lessons = await self.r.lessons(m.id)
            if not lessons:
                errors.append("module without lesson")
            for l in lessons:
                if not await self.r.objectives(l.id):
                    errors.append("lesson without objective")
                for b in await self.r.blocks(l.id):
                    try:
                        safe_content(b.content_json)
                    except CourseError:
                        errors.append("executable content")
                    if b.confidence_class in {
                        ConfidenceClass.CONFIRMED,
                        ConfidenceClass.PROBABLE,
                        ConfidenceClass.INFERRED,
                    } and not await self.r.citations(b.id):
                        errors.append("factual block without citation")
        return errors

    async def publish(self, version_id: UUID) -> CourseVersion:
        version = await self.r.get_version(version_id)
        if not version:
            raise CourseError("COURSE_VERSION_NOT_FOUND", "Version not found")
        if version.status is not CourseVersionStatus.DRAFT:
            raise CourseError("COURSE_VERSION_IMMUTABLE", "Published version is immutable")
        errors = await self.validate(version_id)
        if errors:
            raise CourseError("COURSE_VERSION_VALIDATION_FAILED", "; ".join(errors))
        version.publish()
        return version

    async def copy_as_draft(self, version_id: UUID) -> CourseVersion:
        old = await self.r.get_version(version_id)
        if not old:
            raise CourseError("COURSE_VERSION_NOT_FOUND", "Version not found")
        new = CourseVersion(
            old.course_id,
            len(await self.r.versions(old.course_id)) + 1,
            old.title,
            old.description,
            deepcopy(dict(old.content_json)),
            old.created_by,
            parent_version_id=old.id,
        )
        await self.r.add_version(new, None)
        for old_module in await self.r.modules(old.id):
            module = Module(
                new.id,
                old_module.position,
                old_module.title,
                old_module.skill_ids,
                old_module.description,
                old_module.estimated_duration_minutes,
                old_module.prerequisite_module_ids,
            )
            await self.r.add_module(module)
            for old_lesson in await self.r.lessons(old_module.id):
                lesson = Lesson(
                    module.id,
                    old_lesson.position,
                    old_lesson.title,
                    old_lesson.summary,
                    prerequisite_skill_ids=old_lesson.prerequisite_skill_ids,
                    estimated_duration_minutes=old_lesson.estimated_duration_minutes,
                )
                await self.r.add_lesson(lesson)
                objective_ids = []
                for objective in await self.r.objectives(old_lesson.id):
                    copied_objective = LearningObjective(
                        objective.objective_text,
                        objective.measurable_verb,
                        objective.bloom_level,
                        objective.linked_skill_ids,
                        objective.linked_claim_ids,
                        lesson.id,
                    )
                    await self.r.add_objective(copied_objective, lesson.id)
                    objective_ids.append(copied_objective.id)
                lesson.learning_objective_ids = tuple(objective_ids)
                for old_block in await self.r.blocks(old_lesson.id):
                    block = ContentBlock(
                        lesson.id,
                        old_block.position,
                        old_block.block_type,
                        deepcopy(old_block.content_json),
                        old_block.confidence_class,
                        old_block.linked_claim_ids,
                        old_block.linked_skill_ids,
                        old_block.evidence_link_ids,
                        old_block.prompt_version,
                        old_block.attribution,
                        old_block.locked,
                    )
                    await self.r.add_block(block)
                    for citation in await self.r.citations(old_block.id):
                        await self.r.add_citation(
                            Citation(
                                citation.project_id,
                                new.id,
                                citation.claim_id,
                                citation.evidence_link_id,
                                citation.source_id,
                                citation.source_snapshot_id,
                                block.id,
                                citation.citation_type,
                            )
                        )
        return new
