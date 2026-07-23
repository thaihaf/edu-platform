"""Framework-neutral Phase 8 assessment question contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import Any, Protocol
from uuid import UUID, uuid4

from packages.domain.models import InvalidStateTransitionError, utcnow


class QuestionError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(message)


class QuestionJobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class QuestionStage(StrEnum):
    VALIDATING_INPUT = "VALIDATING_INPUT"
    SELECTING_OBJECTIVES = "SELECTING_OBJECTIVES"
    SELECTING_EVIDENCE = "SELECTING_EVIDENCE"
    MINING_REPORTED_QUESTIONS = "MINING_REPORTED_QUESTIONS"
    GENERATING_QUESTIONS = "GENERATING_QUESTIONS"
    GENERATING_ANSWERS = "GENERATING_ANSWERS"
    GENERATING_DISTRACTORS = "GENERATING_DISTRACTORS"
    INDEPENDENT_SOLVING = "INDEPENDENT_SOLVING"
    GROUNDING_REVIEW = "GROUNDING_REVIEW"
    AMBIGUITY_REVIEW = "AMBIGUITY_REVIEW"
    DUPLICATE_REVIEW = "DUPLICATE_REVIEW"
    DIFFICULTY_CALIBRATION = "DIFFICULTY_CALIBRATION"
    PERSISTING_DRAFT = "PERSISTING_DRAFT"
    COMPLETED = "COMPLETED"


class QuestionType(StrEnum):
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    ESSAY = "ESSAY"
    CODING = "CODING"
    SQL = "SQL"
    SCENARIO = "SCENARIO"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    INTERVIEW = "INTERVIEW"


class OriginType(StrEnum):
    VERBATIM_REPORTED = "VERBATIM_REPORTED"
    PARAPHRASED_REPORTED = "PARAPHRASED_REPORTED"
    SOURCE_DERIVED = "SOURCE_DERIVED"
    JD_INFERRED = "JD_INFERRED"
    DOMAIN_STANDARD = "DOMAIN_STANDARD"
    AI_SYNTHESIZED = "AI_SYNTHESIZED"
    HUMAN_AUTHORED = "HUMAN_AUTHORED"


class QuestionReviewStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    AUTO_REVIEWED = "AUTO_REVIEWED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"


class QuestionPublicationStatus(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    RETIRED = "RETIRED"


class QuestionBankVersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ValidationType(StrEnum):
    STRUCTURE = "STRUCTURE"
    ANSWER_CORRECTNESS = "ANSWER_CORRECTNESS"
    INDEPENDENT_SOLVER = "INDEPENDENT_SOLVER"
    GROUNDING = "GROUNDING"
    AMBIGUITY = "AMBIGUITY"
    DISTRACTOR_QUALITY = "DISTRACTOR_QUALITY"
    DUPLICATE = "DUPLICATE"
    DIFFICULTY = "DIFFICULTY"
    BLOOM_ALIGNMENT = "BLOOM_ALIGNMENT"
    LANGUAGE_QUALITY = "LANGUAGE_QUALITY"
    ORIGIN_VALIDITY = "ORIGIN_VALIDITY"
    CODE_EXECUTION = "CODE_EXECUTION"
    SQL_EXECUTION = "SQL_EXECUTION"


@dataclass(frozen=True)
class IndependentSolverRequest:
    """Answer-neutral payload crossing the independent-solver boundary."""

    stem: str
    options: tuple[str, ...]
    evidence_context: tuple[str, ...]
    question_type: QuestionType


class IndependentQuestionSolver(Protocol):
    async def solve(self, request: IndependentSolverRequest) -> Any: ...


class ValidationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Difficulty(StrEnum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"


class QuestionBloomLevel(StrEnum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"


class DuplicateClusterType(StrEnum):
    EXACT = "EXACT"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    PARAPHRASE = "PARAPHRASE"
    SAME_CONCEPT_DIFFERENT_DIFFICULTY = "SAME_CONCEPT_DIFFERENT_DIFFICULTY"
    RELATED_NOT_DUPLICATE = "RELATED_NOT_DUPLICATE"


class ReviewDecisionType(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    ACCEPT_REVISION = "ACCEPT_REVISION"
    RETIRE = "RETIRE"
    MARK_DUPLICATE = "MARK_DUPLICATE"
    CONFIRM_REPORTED_ORIGIN = "CONFIRM_REPORTED_ORIGIN"
    REJECT_REPORTED_ORIGIN = "REJECT_REPORTED_ORIGIN"


class RevisionAuthorType(StrEnum):
    AI_GENERATED = "AI_GENERATED"
    AI_REVISED = "AI_REVISED"
    HUMAN_AUTHORED = "HUMAN_AUTHORED"
    HUMAN_REVISED = "HUMAN_REVISED"


def normalized_fingerprint(stem: str) -> str:
    return sha256(" ".join(stem.casefold().split()).encode()).hexdigest()


@dataclass
class QuestionGenerationJob:
    project_id: UUID
    idempotency_key: str
    requested_question_types: tuple[QuestionType, ...]
    requested_count: int
    created_by: UUID
    course_id: UUID | None = None
    course_version_id: UUID | None = None
    module_id: UUID | None = None
    lesson_id: UUID | None = None
    generation_mode: str = "AI_GENERATION"
    difficulty_distribution: dict[str, int] = field(default_factory=dict)
    bloom_distribution: dict[str, int] = field(default_factory=dict)
    origin_policy: dict[str, Any] = field(default_factory=dict)
    model_call_budget: int = 20
    token_budget: int | None = None
    cost_budget: float | None = None
    request_fingerprint: str = ""
    policy_version: str = "question-policy-v1"
    prompt_version: str = "question-v1"
    id: UUID = field(default_factory=uuid4)
    status: QuestionJobStatus = QuestionJobStatus.PENDING
    current_stage: QuestionStage = QuestionStage.VALIDATING_INPUT
    progress_percent: int = 0
    generated_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    model_calls_used: int = 0
    tokens_used: int | None = None
    estimated_cost: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    started_at: Any = None
    completed_at: Any = None
    failed_at: Any = None
    cancelled_at: Any = None
    created_at: Any = field(default_factory=utcnow)
    updated_at: Any = field(default_factory=utcnow)

    def advance(self, stage: QuestionStage, progress: int) -> None:
        if self.status in {
            QuestionJobStatus.COMPLETED,
            QuestionJobStatus.FAILED,
            QuestionJobStatus.CANCELLED,
        } or list(QuestionStage).index(stage) < list(QuestionStage).index(self.current_stage):
            raise InvalidStateTransitionError("Invalid question generation transition")
        self.status, self.current_stage, self.progress_percent, self.started_at, self.updated_at = (
            QuestionJobStatus.RUNNING,
            stage,
            progress,
            self.started_at or utcnow(),
            utcnow(),
        )

    def complete(self) -> None:
        self.advance(QuestionStage.COMPLETED, 100)
        self.status, self.completed_at = QuestionJobStatus.COMPLETED, utcnow()

    def fail(self, code: str, message: str) -> None:
        self.status, self.error_code, self.error_message, self.failed_at, self.updated_at = (
            QuestionJobStatus.FAILED,
            code,
            message,
            utcnow(),
            utcnow(),
        )

    def cancel(self) -> None:
        self.status, self.cancelled_at = QuestionJobStatus.CANCELLED, utcnow()


@dataclass
class QuestionBank:
    project_id: UUID
    title: str
    description: str
    locale: str = "en"
    course_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)
    updated_at: Any = field(default_factory=utcnow)


@dataclass
class QuestionBankVersion:
    question_bank_id: UUID
    version_number: int
    created_by: UUID
    parent_version_id: UUID | None = None
    source_course_version_id: UUID | None = None
    generation_job_id: UUID | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    status: QuestionBankVersionStatus = QuestionBankVersionStatus.DRAFT
    created_at: Any = field(default_factory=utcnow)
    published_at: Any = None
    archived_at: Any = None

    def publish(self) -> None:
        if self.status is not QuestionBankVersionStatus.DRAFT:
            raise QuestionError("QUESTION_BANK_VERSION_IMMUTABLE", "Only drafts may be published")
        self.status, self.published_at = QuestionBankVersionStatus.PUBLISHED, utcnow()


@dataclass
class QuestionBlueprint:
    generation_job_id: UUID
    target_objective_id: UUID | None
    target_skill_ids: tuple[UUID, ...]
    target_claim_ids: tuple[UUID, ...]
    question_type: QuestionType
    intended_difficulty: Difficulty
    intended_bloom_level: QuestionBloomLevel
    tested_concepts: tuple[str, ...]
    origin_type: OriginType
    generation_rationale: str
    evidence_requirements: tuple[UUID, ...] = ()
    misconception_targets: tuple[str, ...] = ()
    status: str = "DRAFT"
    id: UUID = field(default_factory=uuid4)

    @property
    def fingerprint(self) -> str:
        return normalized_fingerprint("|".join((*self.tested_concepts, self.question_type)))


@dataclass
class Question:
    question_bank_version_id: UUID
    question_type: QuestionType
    stem: str
    answer_json: dict[str, Any]
    explanation: str
    difficulty: Difficulty
    bloom_level: QuestionBloomLevel
    origin_type: OriginType
    linked_objective_ids: tuple[UUID, ...] = ()
    linked_skill_ids: tuple[UUID, ...] = ()
    linked_claim_ids: tuple[UUID, ...] = ()
    source_evidence_link_ids: tuple[UUID, ...] = ()
    citation_ids: tuple[UUID, ...] = ()
    linked_reported_question_id: UUID | None = None
    origin_confidence: float = 0
    generation_metadata: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    normalized_fingerprint: str = ""
    review_status: QuestionReviewStatus = QuestionReviewStatus.UNREVIEWED
    publication_status: QuestionPublicationStatus = QuestionPublicationStatus.DRAFT
    created_at: Any = field(default_factory=utcnow)
    updated_at: Any = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        self.normalized_fingerprint = self.normalized_fingerprint or normalized_fingerprint(
            self.stem
        )


@dataclass(frozen=True)
class QuestionOption:
    question_id: UUID
    position: int
    option_text: str
    is_correct: bool
    explanation: str = ""
    distractor_rationale: str = ""
    misconception_code: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass(frozen=True)
class QuestionCitation:
    question_id: UUID
    evidence_link_id: UUID
    source_id: UUID
    source_snapshot_id: UUID
    source_chunk_ids: tuple[UUID, ...]
    claim_id: UUID | None = None
    page_reference: str | None = None
    section_reference: str | None = None
    extracted_span: str | None = None
    citation_type: str = "DIRECT"
    origin_scope_metadata: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass(frozen=True)
class QuestionValidationResult:
    question_id: UUID
    validator_type: ValidationType
    status: ValidationStatus
    reasons: tuple[str, ...] = ()
    score: float | None = None
    proposed_revision: str | None = None
    model_metadata: dict[str, Any] | None = None
    policy_version: str = "question-policy-v1"
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass(frozen=True)
class QuestionReviewDecision:
    project_id: UUID
    reviewer_id: UUID
    question_id: UUID
    decision: ReviewDecisionType
    reason: str
    previous_status: QuestionReviewStatus
    new_status: QuestionReviewStatus
    revision_json: dict[str, Any] | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass(frozen=True)
class QuestionRevision:
    question_id: UUID
    revision_number: int
    stem: str
    answer_json: dict[str, Any]
    explanation: str
    options_json: tuple[dict[str, Any], ...]
    origin_type: OriginType
    linked_evidence_ids: tuple[UUID, ...]
    author_type: RevisionAuthorType
    created_by: UUID
    previous_revision_id: UUID | None = None
    model_metadata: dict[str, Any] | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)
