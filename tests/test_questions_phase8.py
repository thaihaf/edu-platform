import asyncio
from uuid import uuid4

import pytest

from packages.application.questions import QuestionService, fingerprint
from packages.domain.evidence import (
    EvidenceLink,
    EvidenceRelation,
    QuestionOriginType,
    ReportedQuestion,
    ReviewStatus,
)
from packages.domain.question import (
    Difficulty,
    IndependentSolverRequest,
    OriginType,
    Question,
    QuestionBank,
    QuestionError,
    QuestionOption,
    QuestionPublicationStatus,
    QuestionReviewStatus,
    QuestionType,
    QuestionBloomLevel,
    ReviewDecisionType,
    ValidationStatus,
    ValidationType,
)
from packages.infrastructure.question import (
    DisabledCodeExecutionSandbox,
    InMemoryQuestionRepository,
)


def test_project_scoped_idempotency_allows_same_key_in_two_projects() -> None:
    async def run() -> None:
        repo = InMemoryQuestionRepository()
        service = QuestionService(repo)
        actor = uuid4()
        key = "same-key"
        first = await service.start(
            __import__(
                "packages.domain.question", fromlist=["QuestionGenerationJob"]
            ).QuestionGenerationJob(
                uuid4(),
                key,
                (QuestionType.SHORT_ANSWER,),
                1,
                actor,
                request_fingerprint=fingerprint({"x": 1}),
            )
        )
        second = await service.start(
            __import__(
                "packages.domain.question", fromlist=["QuestionGenerationJob"]
            ).QuestionGenerationJob(
                uuid4(),
                key,
                (QuestionType.SHORT_ANSWER,),
                1,
                actor,
                request_fingerprint=fingerprint({"x": 1}),
            )
        )
        assert first.id != second.id
        assert (
            await service.start(
                __import__(
                    "packages.domain.question", fromlist=["QuestionGenerationJob"]
                ).QuestionGenerationJob(
                    first.project_id,
                    key,
                    (QuestionType.SHORT_ANSWER,),
                    1,
                    actor,
                    request_fingerprint=fingerprint({"x": 1}),
                )
            )
            is first
        )
        with pytest.raises(QuestionError, match="payload differs"):
            await service.start(
                __import__(
                    "packages.domain.question", fromlist=["QuestionGenerationJob"]
                ).QuestionGenerationJob(
                    first.project_id,
                    key,
                    (QuestionType.SHORT_ANSWER,),
                    1,
                    actor,
                    request_fingerprint=fingerprint({"x": 2}),
                )
            )
        with pytest.raises(QuestionError, match="disabled"):
            await DisabledCodeExecutionSandbox().execute("x")

    asyncio.run(run())


def test_non_choice_answers_require_meaningful_rubric() -> None:
    async def run() -> None:
        repo = InMemoryQuestionRepository()
        service = QuestionService(repo)
        version = await service.create_bank(QuestionBank(uuid4(), "Bank", ""), uuid4())
        empty = Question(
            version.id,
            QuestionType.ESSAY,
            "Explain caching.",
            {},
            "",
            Difficulty.MEDIUM,
            QuestionBloomLevel.UNDERSTAND,
            OriginType.HUMAN_AUTHORED,
        )
        await service.add_question(empty)
        assert any(
            result.validator_type is ValidationType.ANSWER_CORRECTNESS
            and result.status is ValidationStatus.FAIL
            for result in repo.validations[empty.id]
        )
        rubric = Question(
            version.id,
            QuestionType.SYSTEM_DESIGN,
            "Design a cache.",
            {"rubric": ["addresses invalidation"]},
            "",
            Difficulty.HARD,
            QuestionBloomLevel.CREATE,
            OriginType.HUMAN_AUTHORED,
        )
        await service.add_question(rubric)
        assert all(result.status is ValidationStatus.PASS for result in repo.validations[rubric.id])

    asyncio.run(run())


def test_rejection_and_requested_changes_revoke_approval() -> None:
    async def run() -> None:
        repo = InMemoryQuestionRepository()
        service = QuestionService(repo)
        actor = uuid4()
        version = await service.create_bank(QuestionBank(uuid4(), "Bank", ""), actor)
        for decision in (ReviewDecisionType.REJECT, ReviewDecisionType.REQUEST_CHANGES):
            q = Question(
                version.id,
                QuestionType.SHORT_ANSWER,
                "Explain scope.",
                {"rubric": "specific explanation"},
                "",
                Difficulty.MEDIUM,
                QuestionBloomLevel.UNDERSTAND,
                OriginType.HUMAN_AUTHORED,
            )
            await service.add_question(q)
            await service.review(q.id, actor, ReviewDecisionType.APPROVE, "approved")
            assert q.publication_status is QuestionPublicationStatus.APPROVED
            await service.review(q.id, actor, decision, "not ready")
            assert q.publication_status is QuestionPublicationStatus.DRAFT
            assert q.review_status is not QuestionReviewStatus.HUMAN_APPROVED
            assert not repo.validations[q.id]

    asyncio.run(run())


def test_materialized_reported_question_persists_direct_immutable_citations() -> None:
    async def run() -> None:
        repo = InMemoryQuestionRepository()
        service = QuestionService(repo)
        project = uuid4()
        version = await service.create_bank(QuestionBank(project, "Bank", ""), uuid4())
        claim, source, snapshot, chunk = uuid4(), uuid4(), uuid4(), uuid4()
        link = EvidenceLink(
            project,
            claim,
            source,
            snapshot,
            (chunk,),
            EvidenceRelation.SUPPORTS,
            1,
            1,
            None,
            1,
            extracted_span="quoted text",
            page_reference="p. 4",
            section_reference="Methods",
        )
        await repo.add_evidence_link(link)
        reported = ReportedQuestion(
            project,
            "What was measured?",
            QuestionOriginType.VERBATIM_REPORTED,
            (link.id,),
            review_status=ReviewStatus.HUMAN_APPROVED,
        )
        q = await service.materialize_reported(project, reported, version.id, "reported-key")
        citation = repo.citations[q.id][0]
        assert (
            citation.evidence_link_id,
            citation.source_id,
            citation.source_snapshot_id,
            citation.source_chunk_ids,
            citation.claim_id,
        ) == (link.id, source, snapshot, (chunk,), claim)
        assert (citation.page_reference, citation.section_reference, citation.extracted_span) == (
            "p. 4",
            "Methods",
            "quoted text",
        )
        assert citation.origin_scope_metadata["reported_question_id"] == str(reported.id)

    asyncio.run(run())


def test_independent_solver_receives_only_sanitized_request() -> None:
    async def run() -> None:
        class Solver:
            request: IndependentSolverRequest

            async def solve(self, request: IndependentSolverRequest):
                self.request = request
                return {"answer": "A"}

        solver = Solver()
        repo = InMemoryQuestionRepository()
        service = QuestionService(repo, solver)
        version = await service.create_bank(QuestionBank(uuid4(), "Bank", ""), uuid4())
        q = Question(
            version.id,
            QuestionType.SINGLE_CHOICE,
            "Choose A.",
            {"answer": "A"},
            "The answer is A",
            Difficulty.EASY,
            QuestionBloomLevel.REMEMBER,
            OriginType.HUMAN_AUTHORED,
            generation_metadata={"proposed_answer": "A"},
        )
        await service.add_question(
            q,
            [
                QuestionOption(q.id, 1, "A", True, "reveals answer"),
                QuestionOption(q.id, 2, "B", False),
            ],
        )
        assert solver.request.options == ("A", "B")
        assert not hasattr(solver.request, "answer_json") and not hasattr(
            solver.request, "generation_metadata"
        )

    asyncio.run(run())


def test_ambiguity_failure_blocks_approval_and_publication() -> None:
    async def run() -> None:
        repo = InMemoryQuestionRepository()
        service = QuestionService(repo)
        actor = uuid4()
        version = await service.create_bank(QuestionBank(uuid4(), "Bank", ""), actor)
        q = Question(
            version.id,
            QuestionType.SINGLE_CHOICE,
            "What is the best practice currently?",
            {"answer": "A"},
            "",
            Difficulty.EASY,
            QuestionBloomLevel.REMEMBER,
            OriginType.HUMAN_AUTHORED,
        )
        await service.add_question(
            q, [QuestionOption(q.id, 1, "A", True), QuestionOption(q.id, 2, "B", False)]
        )
        assert any(
            x.validator_type is ValidationType.AMBIGUITY and x.status is ValidationStatus.FAIL
            for x in repo.validations[q.id]
        )
        await service.review(q.id, actor, ReviewDecisionType.APPROVE, "attempt")
        assert q.publication_status is QuestionPublicationStatus.DRAFT
        with pytest.raises(QuestionError, match="approved"):
            await service.publish(version.id)

    asyncio.run(run())
