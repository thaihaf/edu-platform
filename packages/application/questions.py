"""Deterministic policies and use cases for validated assessment questions."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from typing import Any
from uuid import UUID

from packages.domain.evidence import ClaimStatus, QuestionOriginType, ReportedQuestion, ReviewStatus
from packages.domain.question import *


def fingerprint(value: Any) -> str: return sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
def _result(question: Question, kind: ValidationType, ok: bool, *reasons: str) -> QuestionValidationResult: return QuestionValidationResult(question.id, kind, ValidationStatus.PASS if ok else ValidationStatus.FAIL, tuple(reasons))


class QuestionService:
    def __init__(self, repository: Any) -> None: self.r = repository
    async def start(self, job: QuestionGenerationJob) -> QuestionGenerationJob:
        if job.requested_count < 1 or not job.requested_question_types: raise QuestionError("QUESTION_GENERATION_INPUT_INVALID", "A count and question type are required")
        old = await self.r.job_by_key(job.idempotency_key)
        if old:
            if old.request_fingerprint != job.request_fingerprint: raise QuestionError("IDEMPOTENCY_CONFLICT", "Idempotency key payload differs")
            return old
        await self.r.add_job(job); return job
    async def create_bank(self, bank: QuestionBank, actor: UUID) -> QuestionBankVersion:
        await self.r.add_bank(bank); version = QuestionBankVersion(bank.id, 1, actor); await self.r.add_version(version); return version
    async def create_version(self, bank_id: UUID, actor: UUID) -> QuestionBankVersion:
        if not await self.r.get_bank(bank_id): raise QuestionError("QUESTION_BANK_NOT_FOUND", "Question bank not found")
        version = QuestionBankVersion(bank_id, len(await self.r.versions_for_bank(bank_id)) + 1, actor); await self.r.add_version(version); return version
    async def validate_blueprint(self, blueprint: QuestionBlueprint, objectives: set[UUID], skills: set[UUID], claims: dict[UUID, Any], links: dict[UUID, list[Any]]) -> None:
        if blueprint.target_objective_id is not None and blueprint.target_objective_id not in objectives: raise QuestionError("QUESTION_GENERATION_INPUT_INVALID", "Blueprint objective does not exist")
        if not set(blueprint.target_skill_ids) <= skills: raise QuestionError("QUESTION_GENERATION_INPUT_INVALID", "Blueprint skill does not exist")
        for claim_id in blueprint.target_claim_ids:
            if claim_id not in claims or claims[claim_id].status not in {ClaimStatus.VERIFIED, ClaimStatus.PROBABLE} or not links.get(claim_id): raise QuestionError("QUESTION_GROUNDING_FAILED", "Blueprint factual claim lacks approved evidence")
    async def add_question(self, question: Question, options: list[QuestionOption] | None = None, citations: list[QuestionCitation] | None = None) -> Question:
        version = await self.r.get_version(question.question_bank_version_id)
        if not version: raise QuestionError("QUESTION_BANK_VERSION_NOT_FOUND", "Question-bank version not found")
        if version.status is not QuestionBankVersionStatus.DRAFT: raise QuestionError("QUESTION_BANK_VERSION_IMMUTABLE", "Published versions are immutable")
        await self.r.add_question(question)
        for option in options or []: await self.r.add_option(option)
        for citation in citations or []: await self.r.add_citation(citation)
        await self.validate_question(question.id); return question
    async def validate_question(self, question_id: UUID, solver_answer: Any = None) -> list[QuestionValidationResult]:
        q = await self.r.get_question(question_id)
        if not q: raise QuestionError("QUESTION_NOT_FOUND", "Question not found")
        options = self.r.options[q.id]; results = [_result(q, ValidationType.STRUCTURE, bool(q.stem.strip()), "stem required"), _result(q, ValidationType.ORIGIN_VALIDITY, q.origin_type in set(OriginType), "invalid origin")]
        if q.question_type is QuestionType.SINGLE_CHOICE: results += [_result(q, ValidationType.ANSWER_CORRECTNESS, sum(o.is_correct for o in options) == 1, "single choice requires exactly one correct option"), _result(q, ValidationType.DISTRACTOR_QUALITY, all(o.option_text.casefold() not in {"all of the above", "none of the above"} for o in options), "unsupported catch-all distractor")]
        if q.question_type is QuestionType.MULTIPLE_CHOICE: results.append(_result(q, ValidationType.ANSWER_CORRECTNESS, 0 < sum(o.is_correct for o in options) < len(options), "multiple choice requires a non-total correct set"))
        if q.origin_type in {OriginType.SOURCE_DERIVED, OriginType.VERBATIM_REPORTED, OriginType.PARAPHRASED_REPORTED}: results.append(_result(q, ValidationType.GROUNDING, bool(self.r.citations[q.id]), "source-derived question requires citation"))
        if q.origin_type in {OriginType.VERBATIM_REPORTED, OriginType.PARAPHRASED_REPORTED}: results.append(_result(q, ValidationType.ORIGIN_VALIDITY, bool(q.linked_reported_question_id and self.r.citations[q.id]), "reported origin requires direct evidence"))
        if q.question_type in {QuestionType.CODING, QuestionType.SQL}: results.append(_result(q, ValidationType.CODE_EXECUTION if q.question_type is QuestionType.CODING else ValidationType.SQL_EXECUTION, False, "execution sandbox unavailable"))
        if solver_answer is not None: results.append(_result(q, ValidationType.INDEPENDENT_SOLVER, solver_answer == q.answer_json, "solver must receive stem only and agree"))
        for r in results: await self.r.add_validation(r)
        return results
    async def publish(self, version_id: UUID) -> QuestionBankVersion:
        version = await self.r.get_version(version_id)
        if not version: raise QuestionError("QUESTION_BANK_VERSION_NOT_FOUND", "Question-bank version not found")
        for q in await self.r.questions_for_version(version_id):
            latest = {}
            for result in self.r.validations[q.id]:
                latest[result.validator_type] = result
            if q.publication_status is not QuestionPublicationStatus.APPROVED or any(result.status is ValidationStatus.FAIL for result in latest.values()): raise QuestionError("QUESTION_NOT_APPROVED", "Every question must be approved with passing gates")
        version.publish(); return version
    async def review(self, question_id: UUID, reviewer: UUID, decision: ReviewDecisionType, reason: str) -> Question:
        q = await self.r.get_question(question_id)
        if not q: raise QuestionError("QUESTION_NOT_FOUND", "Question not found")
        version = await self.r.get_version(q.question_bank_version_id)
        if not version or version.status is not QuestionBankVersionStatus.DRAFT: raise QuestionError("QUESTION_BANK_VERSION_IMMUTABLE", "Published version is immutable")
        old = q.review_status; new = QuestionReviewStatus.HUMAN_APPROVED if decision in {ReviewDecisionType.APPROVE, ReviewDecisionType.ACCEPT_REVISION} else QuestionReviewStatus.HUMAN_REJECTED if decision is ReviewDecisionType.REJECT else QuestionReviewStatus.NEEDS_REVIEW
        q.review_status = new
        if new is QuestionReviewStatus.HUMAN_APPROVED and not any(x.status is ValidationStatus.FAIL for x in self.r.validations[q.id]): q.publication_status = QuestionPublicationStatus.APPROVED
        if decision is ReviewDecisionType.RETIRE: q.publication_status = QuestionPublicationStatus.RETIRED
        bank = await self.r.get_bank(version.question_bank_id); await self.r.add_decision(QuestionReviewDecision(bank.project_id, reviewer, q.id, decision, reason, old, new)); return q
    async def copy_as_draft(self, version_id: UUID, actor: UUID) -> QuestionBankVersion:
        old = await self.r.get_version(version_id)
        if not old: raise QuestionError("QUESTION_BANK_VERSION_NOT_FOUND", "Question-bank version not found")
        new = QuestionBankVersion(old.question_bank_id, len(await self.r.versions_for_bank(old.question_bank_id)) + 1, actor, old.id, old.source_course_version_id, metadata_json=deepcopy(old.metadata_json)); await self.r.add_version(new)
        for source in await self.r.questions_for_version(old.id):
            clone = Question(new.id, source.question_type, source.stem, deepcopy(source.answer_json), source.explanation, source.difficulty, source.bloom_level, source.origin_type, tuple(source.linked_objective_ids), tuple(source.linked_skill_ids), tuple(source.linked_claim_ids), tuple(source.source_evidence_link_ids), (), source.linked_reported_question_id, source.origin_confidence, deepcopy(source.generation_metadata)); await self.r.add_question(clone)
            for o in self.r.options[source.id]: await self.r.add_option(QuestionOption(clone.id, o.position, o.option_text, o.is_correct, o.explanation, o.distractor_rationale, o.misconception_code))
            for c in self.r.citations[source.id]: await self.r.add_citation(QuestionCitation(clone.id, c.evidence_link_id, c.source_id, c.source_snapshot_id, tuple(c.source_chunk_ids), c.claim_id, c.page_reference, c.section_reference, c.extracted_span, c.citation_type))
        return new
    async def materialize_reported(self, project_id: UUID, reported: ReportedQuestion, version_id: UUID, idempotency_key: str) -> Question:
        if reported.project_id != project_id or reported.review_status is not ReviewStatus.HUMAN_APPROVED or not reported.source_evidence_link_ids: raise QuestionError("REPORTED_QUESTION_EVIDENCE_REQUIRED", "Approved direct reported-question evidence is required")
        existing = await self.r.job_by_key(idempotency_key)
        if existing: raise QuestionError("IDEMPOTENCY_CONFLICT", "Materialization key already used")
        q = Question(version_id, QuestionType.SHORT_ANSWER, reported.original_text or reported.normalized_text, {}, "Answer unresolved; human review required.", Difficulty.MEDIUM, QuestionBloomLevel.REMEMBER, OriginType(reported.origin_type), linked_reported_question_id=reported.id, source_evidence_link_ids=reported.source_evidence_link_ids)
        await self.add_question(q); return q
