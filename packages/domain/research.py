"""Framework- and provider-independent Phase 5 research contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any, Protocol
from uuid import UUID, uuid4

from packages.domain.search import QueryFamily


def utcnow() -> datetime:
    return datetime.now(UTC)


class ResearchStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ResearchPhase(StrEnum):
    SCOPING = "SCOPING"
    PLANNING = "PLANNING"
    DISCOVERING = "DISCOVERING"
    SELECTING = "SELECTING"
    FETCHING = "FETCHING"
    PARSING = "PARSING"
    EXTRACTING = "EXTRACTING"
    CONSOLIDATING = "CONSOLIDATING"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    FOLLOWUP_RESEARCH = "FOLLOWUP_RESEARCH"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"


class ObservationType(StrEnum):
    CLAIM_CANDIDATE = "CLAIM_CANDIDATE"
    REPORTED_QUESTION_CANDIDATE = "REPORTED_QUESTION_CANDIDATE"
    EXAM_PATTERN_CANDIDATE = "EXAM_PATTERN_CANDIDATE"
    INTERVIEW_PATTERN_CANDIDATE = "INTERVIEW_PATTERN_CANDIDATE"
    SKILL_REQUIREMENT_CANDIDATE = "SKILL_REQUIREMENT_CANDIDATE"
    TECHNOLOGY_CANDIDATE = "TECHNOLOGY_CANDIDATE"
    WARNING_OR_TIP = "WARNING_OR_TIP"
    SOURCE_REFERENCE = "SOURCE_REFERENCE"
    CONTRADICTION_CANDIDATE = "CONTRADICTION_CANDIDATE"
    UNKNOWN = "UNKNOWN"


class ResearchError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(message)


@dataclass
class ResearchBudget:
    query_budget: int = 20
    source_budget: int = 20
    model_call_budget: int = 20
    max_followup_rounds: int = 2
    queries_used: int = 0
    sources_discovered: int = 0
    sources_selected: int = 0
    sources_fetched: int = 0
    model_calls_used: int = 0
    token_budget: int | None = None
    tokens_used: int | None = None
    cost_budget: float | None = None
    estimated_cost: float | None = None


@dataclass
class ResearchJob:
    project_id: UUID
    created_by: UUID
    idempotency_key: str
    trace_id: str
    research_depth: int = 1
    status: ResearchStatus = ResearchStatus.PENDING
    current_phase: ResearchPhase = ResearchPhase.SCOPING
    current_node: str = "understand_goal"
    progress_percent: int = 0
    retry_count: int = 0
    max_retries: int = 3
    followup_round: int = 0
    budgets: ResearchBudget = field(default_factory=ResearchBudget)
    error_code: str | None = None
    error_message: str | None = None
    workflow_version: str = "phase5.v1"
    policy_version: str = "phase5.v1"
    request_hash: str = ""
    cancellation_requested: bool = False
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    cancelled_at: datetime | None = None

    def transition(self, status: ResearchStatus) -> None:
        allowed = {
            ResearchStatus.PENDING: {ResearchStatus.RUNNING, ResearchStatus.CANCELLED},
            ResearchStatus.RUNNING: {
                ResearchStatus.PAUSED,
                ResearchStatus.COMPLETED,
                ResearchStatus.FAILED,
                ResearchStatus.CANCELLED,
            },
            ResearchStatus.PAUSED: {ResearchStatus.RUNNING, ResearchStatus.CANCELLED},
            ResearchStatus.FAILED: {ResearchStatus.RUNNING},
            ResearchStatus.COMPLETED: set(),
            ResearchStatus.CANCELLED: set(),
        }
        if status not in allowed[self.status]:
            raise ResearchError(
                "INVALID_RESEARCH_TRANSITION", f"Cannot transition {self.status} to {status}"
            )
        self.status = status
        self.updated_at = utcnow()
        self.started_at = self.started_at or utcnow()
        if status is ResearchStatus.COMPLETED:
            self.completed_at = utcnow()
        if status is ResearchStatus.FAILED:
            self.failed_at = utcnow()
        if status is ResearchStatus.CANCELLED:
            self.cancelled_at = utcnow()


@dataclass(frozen=True)
class ResearchBrief:
    normalized_goal: str
    target_organization: str | None
    target_role: str | None
    target_assessment_types: tuple[str, ...]
    expected_outcome: str
    learner_profile_summary: str | None
    locale: str
    time_range: str | None
    known_constraints: tuple[str, ...]
    required_research_questions: tuple[str, ...]
    required_source_categories: tuple[str, ...] = ("OFFICIAL", "CANDIDATE_REPORT", "DOCUMENT")
    preferred_source_categories: tuple[str, ...] = ()
    excluded_source_categories: tuple[str, ...] = ()
    known_initial_sources: tuple[str, ...] = ()
    uncertainty_areas: tuple[str, ...] = ()
    contradiction_searches: tuple[str, ...] = ()
    stop_criteria: tuple[str, ...] = ()
    legal_access_constraints: tuple[str, ...] = ("public sources only", "robots respected")


@dataclass(frozen=True)
class PlannedQuery:
    text: str
    family: QueryFamily
    purpose: str
    expected_source_type: str
    priority: int
    language: str | None = None
    time_range: str | None = None
    domain_filters: tuple[str, ...] = ()
    file_type_filters: tuple[str, ...] = ()
    parent_question: str | None = None
    estimated_value: float = 0.0
    execution_status: str = "PENDING"
    id: UUID = field(default_factory=uuid4)

    @property
    def fingerprint(self) -> str:
        return sha256(" ".join(self.text.lower().split()).encode()).hexdigest()


@dataclass(frozen=True)
class SourceSelection:
    source_id: UUID
    selected: bool
    reason: str
    rejection_reason: str | None = None
    expected_information_gain: float = 0.0


@dataclass(frozen=True)
class ResearchObservation:
    project_id: UUID
    research_job_id: UUID
    source_id: UUID
    source_snapshot_id: UUID | None
    observation_type: ObservationType
    normalized_text: str
    source_chunk_ids: tuple[UUID, ...] = ()
    verbatim_span: str | None = None
    section_reference: str | None = None
    directness: float = 0.0
    extraction_confidence: float = 0.0
    temporal_reference: str | None = None
    entities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    model: str = "deterministic"
    prompt_version: str = "phase5.v1"
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if (
            self.observation_type is ObservationType.REPORTED_QUESTION_CANDIDATE
            and not self.verbatim_span
        ):
            raise ResearchError(
                "RESEARCH_EXTRACTION_FAILED", "Reported-question candidates require a source span"
            )


@dataclass(frozen=True)
class ResearchGap:
    description: str
    gap_type: str
    severity: str
    affected_research_questions: tuple[str, ...]
    missing_source_types: tuple[str, ...]
    recommended_query_families: tuple[QueryFamily, ...]
    suggested_queries: tuple[str, ...]
    estimated_value: float
    status: str = "OPEN"


@dataclass(frozen=True)
class CoverageReport:
    required_question_coverage: float
    source_category_coverage: float
    temporal_coverage: float
    entity_coverage: float
    query_family_coverage: float
    official_source_coverage: bool
    candidate_report_coverage: bool
    document_coverage: bool
    contradiction_coverage: bool
    unresolved_areas: tuple[str, ...] = ()
    weakly_supported_areas: tuple[str, ...] = ()
    failed_source_impact: tuple[str, ...] = ()
    marginal_information_gain: float = 0.0


@dataclass
class ResearchState:
    research_job_id: UUID
    project_id: UUID
    user_goal: str
    locale: str
    research_policy: dict[str, Any]
    learner_context: str | None = None
    time_range: str | None = None
    assessment_context: dict[str, Any] | None = None
    research_brief: ResearchBrief | None = None
    entity_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)
    research_questions: tuple[str, ...] = ()
    planned_queries: tuple[PlannedQuery, ...] = ()
    executed_query_ids: tuple[UUID, ...] = ()
    search_result_ids: tuple[UUID, ...] = ()
    selected_source_ids: tuple[UUID, ...] = ()
    fetched_snapshot_ids: tuple[UUID, ...] = ()
    parsed_snapshot_ids: tuple[UUID, ...] = ()
    extraction_artifact_ids: tuple[UUID, ...] = ()
    coverage: CoverageReport | None = None
    gaps: tuple[ResearchGap, ...] = ()
    unresolved_observations: tuple[str, ...] = ()
    current_followup_round: int = 0
    budgets: ResearchBudget = field(default_factory=ResearchBudget)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    final_artifact_id: UUID | None = None
    workflow_version: str = "phase5.v1"

    def serializable(self) -> dict[str, Any]:
        return asdict(self)


class ResearchWorkflow(Protocol):
    async def start(self, job: ResearchJob, state: ResearchState) -> None: ...
    async def resume(self, job_id: UUID) -> None: ...
    async def cancel(self, job_id: UUID) -> None: ...
    async def retry(self, job_id: UUID) -> None: ...
    async def get_state(self, job_id: UUID) -> ResearchState: ...
    async def get_progress(self, job_id: UUID) -> ResearchJob: ...


class ResearchCheckpointStore(Protocol):
    async def save_checkpoint(self, job_id: UUID, node: str, state: ResearchState) -> None: ...
    async def load_checkpoint(self, job_id: UUID, workflow_version: str) -> ResearchState: ...
    async def list_checkpoints(self, job_id: UUID) -> list[str]: ...
    async def mark_terminal(self, job_id: UUID) -> None: ...


class ResearchModel(Protocol):
    async def understand_goal(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...


class ResearchJobRepository(Protocol):
    async def get(self, id: UUID) -> ResearchJob | None: ...
    async def by_key(self, key: str) -> ResearchJob | None: ...
    async def save(self, job: ResearchJob) -> ResearchJob: ...
