"""Deterministic in-memory adapters for the Phase 8 assessment boundary."""

from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from typing import Any
from uuid import UUID

from packages.domain.question import *


class InMemoryQuestionRepository:
    def __init__(self) -> None:
        self.evidence_links: dict[UUID, Any] = {}
        self.jobs: dict[UUID, QuestionGenerationJob] = {}
        self.banks: dict[UUID, QuestionBank] = {}
        self.versions: dict[UUID, QuestionBankVersion] = {}
        self.questions: dict[UUID, Question] = {}
        self.options: dict[UUID, list[QuestionOption]] = defaultdict(list)
        self.citations: dict[UUID, list[QuestionCitation]] = defaultdict(list)
        self.validations: dict[UUID, list[QuestionValidationResult]] = defaultdict(list)
        self.revisions: dict[UUID, list[QuestionRevision]] = defaultdict(list)
        self.decisions: dict[UUID, list[QuestionReviewDecision]] = defaultdict(list)
        self.blueprints: dict[UUID, list[QuestionBlueprint]] = defaultdict(list)
        self.events: dict[UUID, list[dict[str, Any]]] = defaultdict(list)

    async def job_by_key(self, project_id: UUID, key: str) -> QuestionGenerationJob | None:
        return next(
            (
                j
                for j in self.jobs.values()
                if j.project_id == project_id and j.idempotency_key == key
            ),
            None,
        )

    async def add_evidence_link(self, link: Any) -> None:
        self.evidence_links[link.id] = link

    async def get_evidence_link(self, ident: UUID) -> Any | None:
        return self.evidence_links.get(ident)

    async def add_job(self, job: QuestionGenerationJob) -> None:
        self.jobs[job.id] = job

    async def get_job(self, ident: UUID) -> QuestionGenerationJob | None:
        return self.jobs.get(ident)

    async def event(self, job: QuestionGenerationJob, stage: str, payload: dict[str, Any]) -> None:
        self.events[job.id].append({"stage": stage, "payload": deepcopy(payload)})

    async def add_bank(self, bank: QuestionBank) -> None:
        self.banks[bank.id] = bank

    async def get_bank(self, ident: UUID) -> QuestionBank | None:
        return self.banks.get(ident)

    async def banks_for_project(self, project: UUID) -> list[QuestionBank]:
        return [b for b in self.banks.values() if b.project_id == project]

    async def add_version(self, version: QuestionBankVersion) -> None:
        self.versions[version.id] = version

    async def get_version(self, ident: UUID) -> QuestionBankVersion | None:
        return self.versions.get(ident)

    async def versions_for_bank(self, bank: UUID) -> list[QuestionBankVersion]:
        return sorted(
            (v for v in self.versions.values() if v.question_bank_id == bank),
            key=lambda v: v.version_number,
        )

    async def add_blueprint(self, blueprint: QuestionBlueprint) -> None:
        if not any(
            x.fingerprint == blueprint.fingerprint
            for x in self.blueprints[blueprint.generation_job_id]
        ):
            self.blueprints[blueprint.generation_job_id].append(blueprint)

    async def add_question(self, question: Question) -> None:
        self.questions[question.id] = question

    async def get_question(self, ident: UUID) -> Question | None:
        return self.questions.get(ident)

    async def questions_for_version(self, version: UUID) -> list[Question]:
        return [q for q in self.questions.values() if q.question_bank_version_id == version]

    async def project_questions(self, project: UUID) -> list[Question]:
        return [
            q
            for q in self.questions.values()
            if (
                await self.get_bank(
                    (await self.get_version(q.question_bank_version_id)).question_bank_id
                )
            ).project_id
            == project
        ]  # type: ignore[union-attr]

    async def add_option(self, option: QuestionOption) -> None:
        self.options[option.question_id].append(option)

    async def add_citation(self, citation: QuestionCitation) -> None:
        self.citations[citation.question_id].append(citation)

    async def add_validation(self, result: QuestionValidationResult) -> None:
        if not any(
            x.validator_type == result.validator_type
            and x.status == result.status
            and x.reasons == result.reasons
            for x in self.validations[result.question_id]
        ):
            self.validations[result.question_id].append(result)

    async def invalidate_validations(self, question_id: UUID) -> None:
        self.validations[question_id] = []

    async def add_revision(self, revision: QuestionRevision) -> None:
        self.revisions[revision.question_id].append(revision)

    async def add_decision(self, decision: QuestionReviewDecision) -> None:
        self.decisions[decision.question_id].append(decision)


class DisabledCodeExecutionSandbox:
    async def execute(self, *_: Any, **__: Any) -> None:
        raise QuestionError("CODE_SANDBOX_UNAVAILABLE", "Code execution sandbox is disabled")


class DisabledSQLExecutionSandbox:
    async def execute(self, *_: Any, **__: Any) -> None:
        raise QuestionError("SQL_SANDBOX_UNAVAILABLE", "SQL execution sandbox is disabled")
