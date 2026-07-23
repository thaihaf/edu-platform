"""Framework-independent Phase 9 evaluation contracts and policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from json import dumps
from typing import Any, Protocol
from uuid import UUID, uuid4

from packages.domain.models import utcnow


class EvaluationError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(message)


class ArtifactType(StrEnum):
    RESEARCH_RESULT = "RESEARCH_RESULT"
    RESEARCH_OBSERVATION = "RESEARCH_OBSERVATION"
    SOURCE = "SOURCE"
    CLAIM = "CLAIM"
    EVIDENCE_LINK = "EVIDENCE_LINK"
    COURSE_VERSION = "COURSE_VERSION"
    MODULE = "MODULE"
    LESSON = "LESSON"
    CONTENT_BLOCK = "CONTENT_BLOCK"
    QUESTION_BANK_VERSION = "QUESTION_BANK_VERSION"
    QUESTION = "QUESTION"
    RETRIEVAL_RESULT = "RETRIEVAL_RESULT"
    MODEL_OUTPUT = "MODEL_OUTPUT"


class RunStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RunStage(StrEnum):
    VALIDATING_INPUT = "VALIDATING_INPUT"
    LOADING_CASES = "LOADING_CASES"
    RUNNING_DETERMINISTIC_METRICS = "RUNNING_DETERMINISTIC_METRICS"
    RUNNING_MODEL_METRICS = "RUNNING_MODEL_METRICS"
    AGGREGATING = "AGGREGATING"
    APPLYING_QUALITY_GATES = "APPLYING_QUALITY_GATES"
    PERSISTING_REPORT = "PERSISTING_REPORT"
    COMPLETED = "COMPLETED"


class ResultStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    ERROR = "ERROR"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class VersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class GateStatus(StrEnum):
    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    FAILED = "FAILED"
    ERROR = "ERROR"


def config_hash(value: Any) -> str:
    return sha256(
        dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    version: str
    description: str
    artifact_types: tuple[ArtifactType, ...]
    deterministic: bool = True
    provider_type: str = "deterministic"
    score_range: tuple[float, float] = (0, 1)
    default_threshold: float = 1
    configuration_schema: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass
class EvaluationCase:
    dataset_version_id: UUID | None
    case_key: str
    artifact_type: ArtifactType
    input_json: dict[str, Any]
    expected_json: dict[str, Any] | None = None
    required_facts: tuple[str, ...] = ()
    forbidden_claims: tuple[str, ...] = ()
    required_sources: tuple[str, ...] = ()
    rubric: dict[str, Any] = field(default_factory=dict)
    metadata_json: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    difficulty: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)
    updated_at: Any = field(default_factory=utcnow)


@dataclass
class GoldenDataset:
    name: str
    artifact_type: ArtifactType
    locale: str
    description: str = ""
    project_id: UUID | None = None
    domain: str | None = None
    created_by: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)
    updated_at: Any = field(default_factory=utcnow)


@dataclass
class GoldenDatasetVersion:
    dataset_id: UUID
    version_number: int
    changelog: str
    created_by: UUID | None = None
    parent_version_id: UUID | None = None
    status: VersionStatus = VersionStatus.DRAFT
    id: UUID = field(default_factory=uuid4)
    case_count: int = 0
    created_at: Any = field(default_factory=utcnow)
    published_at: Any = None
    archived_at: Any = None


@dataclass
class EvaluationRun:
    artifact_type: ArtifactType
    idempotency_key: str
    project_id: UUID | None = None
    artifact_id: UUID | None = None
    dataset_version_id: UUID | None = None
    metric_set: tuple[tuple[str, str], ...] = ()
    provider_config: dict[str, Any] = field(default_factory=dict)
    quality_gate_policy_id: UUID | None = None
    evaluation_scope: str = "DATASET"
    status: RunStatus = RunStatus.PENDING
    current_stage: RunStage = RunStage.VALIDATING_INPUT
    progress_percent: int = 0
    total_cases: int = 0
    completed_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    warning_cases: int = 0
    model_call_budget: int = 0
    model_calls_used: int = 0
    token_budget: int | None = None
    tokens_used: int | None = None
    cost_budget: float | None = None
    estimated_cost: float | None = None
    policy_version: str = "1"
    evaluator_version: str = "phase-9"
    created_by: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    started_at: Any = None
    completed_at: Any = None
    failed_at: Any = None
    cancelled_at: Any = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: Any = field(default_factory=utcnow)
    updated_at: Any = field(default_factory=utcnow)

    def payload_hash(self) -> str:
        return config_hash(
            {
                "artifact_type": self.artifact_type,
                "artifact_id": self.artifact_id,
                "dataset": self.dataset_version_id,
                "metrics": self.metric_set,
                "config": self.provider_config,
            }
        )


@dataclass(frozen=True)
class EvaluationResult:
    evaluation_run_id: UUID
    artifact_type: ArtifactType
    metric_name: str
    metric_version: str
    status: ResultStatus
    score: float | None
    threshold: float | None
    reasons: tuple[str, ...] = ()
    evidence_json: dict[str, Any] = field(default_factory=dict)
    evaluation_case_id: UUID | None = None
    artifact_id: UUID | None = None
    failure_category: str | None = None
    provider_name: str = "deterministic"
    provider_version: str = "1"
    model_metadata: dict[str, Any] | None = None
    duration_ms: int = 0
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass(frozen=True)
class EvaluationAggregate:
    evaluation_run_id: UUID
    metric_name: str
    metric_version: str
    sample_count: int
    pass_count: int
    fail_count: int
    warning_count: int
    error_count: int
    average_score: float | None
    minimum_score: float | None
    maximum_score: float | None
    percentile_values: dict[str, float]
    metadata_json: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass
class QualityGatePolicy:
    name: str
    artifact_type: ArtifactType
    description: str = ""
    project_id: UUID | None = None
    current_version_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)
    updated_at: Any = field(default_factory=utcnow)


@dataclass
class QualityGatePolicyVersion:
    policy_id: UUID
    version_number: int
    rules_json: list[dict[str, Any]]
    created_by: UUID | None = None
    status: VersionStatus = VersionStatus.DRAFT
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)
    published_at: Any = None


@dataclass(frozen=True)
class QualityGateDecision:
    evaluation_run_id: UUID
    policy_version_id: UUID
    status: GateStatus
    failed_rules: tuple[str, ...] = ()
    warning_rules: tuple[str, ...] = ()
    explanation: str = ""
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass(frozen=True)
class EvaluationBaseline:
    name: str
    artifact_type: ArtifactType
    dataset_version_id: UUID
    evaluation_run_id: UUID
    project_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


@dataclass(frozen=True)
class RegressionComparison:
    current_run_id: UUID
    baseline_run_id: UUID
    metric_deltas: dict[str, float]
    regressions: tuple[str, ...]
    improvements: tuple[str, ...]
    gate_status: GateStatus
    id: UUID = field(default_factory=uuid4)
    created_at: Any = field(default_factory=utcnow)


class DeterministicMetric(Protocol):
    metric_name: str
    metric_version: str
    supported_artifact_types: tuple[ArtifactType, ...]

    def evaluate(
        self, case: EvaluationCase, configuration: dict[str, Any]
    ) -> tuple[ResultStatus, float | None, tuple[str, ...], dict[str, Any]]: ...


class EvaluationProvider(Protocol):
    provider_name: str
    provider_version: str

    def supported_metrics(self) -> tuple[tuple[str, str], ...]: ...
    def evaluate_case(
        self, case: EvaluationCase, metric: DeterministicMetric, configuration: dict[str, Any]
    ) -> EvaluationResult: ...
    def evaluate_batch(
        self,
        cases: tuple[EvaluationCase, ...],
        metric: DeterministicMetric,
        configuration: dict[str, Any],
    ) -> tuple[EvaluationResult, ...]: ...


class JudgeModel(Protocol):
    def score_rubric(self, rubric: dict[str, Any], content: dict[str, Any]) -> dict[str, Any]: ...
    def compare_outputs(
        self, expected: dict[str, Any], actual: dict[str, Any]
    ) -> dict[str, Any]: ...
    def classify_failure(self, content: dict[str, Any]) -> str: ...
    def generate_explanation(self, content: dict[str, Any]) -> str: ...
