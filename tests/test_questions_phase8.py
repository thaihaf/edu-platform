import asyncio
from uuid import uuid4

import pytest

from packages.application.questions import QuestionService, fingerprint
from packages.domain.question import (
    Difficulty, OriginType, Question, QuestionBank, QuestionError, QuestionOption,
    QuestionPublicationStatus, QuestionReviewStatus, QuestionType, ReviewDecisionType,
    QuestionBloomLevel,
)
from packages.infrastructure.question import DisabledCodeExecutionSandbox, InMemoryQuestionRepository


def test_single_choice_requires_exactly_one_correct_answer_and_published_copy_is_independent() -> None:
    async def run() -> None:
        repo = InMemoryQuestionRepository(); service = QuestionService(repo); actor = uuid4()
        version = await service.create_bank(QuestionBank(uuid4(), "Bank", ""), actor)
        question = Question(version.id, QuestionType.SINGLE_CHOICE, "Which answer?", {"option": 1}, "Because.", Difficulty.EASY, QuestionBloomLevel.REMEMBER, OriginType.AI_SYNTHESIZED, linked_objective_ids=(uuid4(),), linked_skill_ids=(uuid4(),))
        await service.add_question(question, [QuestionOption(question.id, 1, "A", True), QuestionOption(question.id, 2, "B", True)])
        assert any(x.status == "FAIL" for x in repo.validations[question.id])
        with pytest.raises(QuestionError, match="approved"):
            await service.publish(version.id)
        repo.options[question.id][1] = QuestionOption(question.id, 2, "B", False)
        await service.validate_question(question.id); question.publication_status = QuestionPublicationStatus.APPROVED; question.review_status = QuestionReviewStatus.HUMAN_APPROVED
        published = await service.publish(version.id); copy = await service.copy_as_draft(published.id, actor)
        copied = (await repo.questions_for_version(copy.id))[0]; copied.answer_json["option"] = 2
        assert question.answer_json["option"] == 1
    asyncio.run(run())


def test_job_idempotency_and_disabled_sandbox() -> None:
    async def run() -> None:
        service = QuestionService(InMemoryQuestionRepository()); project, actor = uuid4(), uuid4()
        from packages.domain.question import QuestionGenerationJob
        job = QuestionGenerationJob(project, "key", (QuestionType.SHORT_ANSWER,), 1, actor, request_fingerprint=fingerprint({"x": 1}))
        assert await service.start(job) is job
        assert await service.start(job) is job
        with pytest.raises(QuestionError, match="disabled"):
            await DisabledCodeExecutionSandbox().execute("x")
    asyncio.run(run())


def test_review_history_is_append_only() -> None:
    async def run() -> None:
        repo = InMemoryQuestionRepository(); service = QuestionService(repo); actor = uuid4(); version = await service.create_bank(QuestionBank(uuid4(), "Bank", ""), actor)
        q = Question(version.id, QuestionType.SHORT_ANSWER, "Explain.", {}, "", Difficulty.MEDIUM, QuestionBloomLevel.UNDERSTAND, OriginType.HUMAN_AUTHORED, linked_objective_ids=(uuid4(),), linked_skill_ids=(uuid4(),))
        await service.add_question(q); await service.review(q.id, actor, ReviewDecisionType.REQUEST_CHANGES, "clarify")
        assert len(repo.decisions[q.id]) == 1 and q.review_status == QuestionReviewStatus.NEEDS_REVIEW
    asyncio.run(run())
