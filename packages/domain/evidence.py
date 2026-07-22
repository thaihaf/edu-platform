"""Framework-neutral Phase 6 evidence and knowledge contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4


def utcnow() -> datetime:
    return datetime.now(UTC)


class ClaimStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    PROBABLE = "PROBABLE"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"
    OBSOLETE = "OBSOLETE"


class ReviewStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    AUTO_REVIEWED = "AUTO_REVIEWED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ClaimType(StrEnum):
    OFFICIAL_REQUIREMENT = "OFFICIAL_REQUIREMENT"
    RECRUITMENT_PROCESS = "RECRUITMENT_PROCESS"
    EXAM_STRUCTURE = "EXAM_STRUCTURE"
    EXAM_PATTERN = "EXAM_PATTERN"
    INTERVIEW_PATTERN = "INTERVIEW_PATTERN"
    TECHNOLOGY_USAGE = "TECHNOLOGY_USAGE"
    SKILL_REQUIREMENT = "SKILL_REQUIREMENT"
    DOMAIN_FACT = "DOMAIN_FACT"
    PREPARATION_TIP = "PREPARATION_TIP"
    TEMPORAL_FACT = "TEMPORAL_FACT"
    SOURCE_LINEAGE = "SOURCE_LINEAGE"
    OTHER = "OTHER"


class EvidenceRelation(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    MENTIONS = "MENTIONS"
    CONTEXTUALIZES = "CONTEXTUALIZES"
    DERIVED_FROM = "DERIVED_FROM"


class ClusterType(StrEnum):
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    SYNDICATED_COPY = "SYNDICATED_COPY"
    COMMON_ORIGIN = "COMMON_ORIGIN"
    UNKNOWN_RELATIONSHIP = "UNKNOWN_RELATIONSHIP"


class QuestionOriginType(StrEnum):
    VERBATIM_REPORTED = "VERBATIM_REPORTED"
    PARAPHRASED_REPORTED = "PARAPHRASED_REPORTED"


class SkillType(StrEnum):
    DOMAIN = "DOMAIN"
    TECHNOLOGY = "TECHNOLOGY"
    CONCEPT = "CONCEPT"
    PROCEDURE = "PROCEDURE"
    TOOL = "TOOL"
    BEHAVIORAL = "BEHAVIORAL"
    ASSESSMENT_STRATEGY = "ASSESSMENT_STRATEGY"


class ReviewDecisionType(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    MARK_DISPUTED = "MARK_DISPUTED"
    MARK_OBSOLETE = "MARK_OBSOLETE"
    MERGE_DUPLICATE = "MERGE_DUPLICATE"
    SPLIT_CLAIM = "SPLIT_CLAIM"
    CONFIRM_RELATION = "CONFIRM_RELATION"
    REJECT_RELATION = "REJECT_RELATION"


class EvidenceError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(message)


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def claim_fingerprint(
    statement: str,
    subjects: tuple[str, ...],
    claim_type: ClaimType,
    temporal_scope: Mapping[str, Any],
) -> str:
    material = "|".join(
        (
            normalize(statement),
            ",".join(sorted(map(normalize, subjects))),
            claim_type.value,
            repr(sorted(temporal_scope.items())),
        )
    )
    return sha256(material.encode()).hexdigest()


@dataclass
class Claim:
    project_id: UUID
    normalized_statement: str
    claim_type: ClaimType
    subject_entities: tuple[str, ...] = ()
    predicate: str | None = None
    object_value: str | None = None
    temporal_scope: Mapping[str, Any] = field(default_factory=dict)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    status: ClaimStatus = ClaimStatus.CANDIDATE
    confidence: float = 0
    confidence_components: Mapping[str, float] = field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    created_from_observation_ids: tuple[UUID, ...] = ()
    normalization_metadata: Mapping[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 1
    supersedes_claim_id: UUID | None = None

    @property
    def fingerprint(self) -> str:
        return claim_fingerprint(
            self.normalized_statement, self.subject_entities, self.claim_type, self.temporal_scope
        )

    def transition(self, target: ClaimStatus, *, verified: bool = False) -> None:
        allowed = {
            ClaimStatus.CANDIDATE: {
                ClaimStatus.PROBABLE,
                ClaimStatus.REJECTED,
                ClaimStatus.DISPUTED,
            },
            ClaimStatus.PROBABLE: {
                ClaimStatus.VERIFIED,
                ClaimStatus.REJECTED,
                ClaimStatus.DISPUTED,
                ClaimStatus.OBSOLETE,
            },
            ClaimStatus.VERIFIED: {ClaimStatus.DISPUTED, ClaimStatus.OBSOLETE},
            ClaimStatus.DISPUTED: {
                ClaimStatus.PROBABLE,
                ClaimStatus.REJECTED,
                ClaimStatus.OBSOLETE,
            },
            ClaimStatus.REJECTED: set(),
            ClaimStatus.OBSOLETE: set(),
        }
        if target not in allowed[self.status] or (target is ClaimStatus.VERIFIED and not verified):
            raise EvidenceError(
                "INVALID_CLAIM_TRANSITION"
                if target is not ClaimStatus.VERIFIED
                else "CLAIM_VERIFICATION_REQUIREMENTS_NOT_MET",
                "Invalid claim transition",
            )
        self.status = target
        self.updated_at = utcnow()


@dataclass(frozen=True)
class EvidenceLink:
    project_id: UUID
    claim_id: UUID
    source_id: UUID
    source_snapshot_id: UUID
    source_chunk_ids: tuple[UUID, ...]
    relation: EvidenceRelation
    directness: float
    strength: float
    independence_cluster_id: UUID | None
    temporal_relevance: float
    observation_id: UUID | None = None
    extracted_span: str | None = None
    page_reference: str | None = None
    section_reference: str | None = None
    reviewer_status: ReviewStatus = ReviewStatus.UNREVIEWED
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if not 0 <= self.directness <= 1 or not 0 <= self.strength <= 1:
            raise EvidenceError("INVALID_EVIDENCE_RELATION", "Evidence scores must be bounded")


@dataclass
class SourceIndependenceCluster:
    project_id: UUID
    cluster_type: ClusterType
    member_source_ids: tuple[UUID, ...]
    similarity_score: float
    lineage_confidence: float
    lineage_reason: str
    canonical_source_id: UUID | None = None
    earliest_known_source_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class ClaimConfidenceAssessment:
    claim_id: UUID
    authority_component: float
    directness_component: float
    freshness_component: float
    specificity_component: float
    independence_component: float
    corroboration_component: float
    contradiction_penalty: float
    commercial_bias_penalty: float
    temporal_relevance_component: float
    reviewer_component: float
    final_confidence: float
    policy_version: str
    explanation: str
    id: UUID = field(default_factory=uuid4)
    calculated_at: datetime = field(default_factory=utcnow)


@dataclass
class ReportedQuestion:
    project_id: UUID
    normalized_text: str
    origin_type: QuestionOriginType
    source_evidence_link_ids: tuple[UUID, ...]
    original_text: str | None = None
    organization: str | None = None
    role: str | None = None
    assessment_type: str | None = None
    appeared_year: int | None = None
    appeared_round: str | None = None
    confidence_appeared: float = 0
    answer_status: str = "NOT_PROVIDED"
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    duplicate_cluster_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class Skill:
    project_id: UUID
    name: str
    normalized_name: str
    description: str
    skill_type: SkillType
    taxonomy_path: tuple[str, ...] = ()
    parent_skill_id: UUID | None = None
    status: str = "CANDIDATE"
    confidence: float = 0
    original_labels: tuple[str, ...] = ()
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class SkillPrerequisite:
    project_id: UUID
    prerequisite_skill_id: UUID
    dependent_skill_id: UUID
    relation_type: str
    confidence: float
    evidence_link_ids: tuple[UUID, ...]
    review_status: ReviewStatus = ReviewStatus.NEEDS_REVIEW
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class KnowledgeGap:
    project_id: UUID
    gap_type: str
    description: str
    severity: str
    affected_claim_ids: tuple[UUID, ...] = ()
    affected_skill_ids: tuple[UUID, ...] = ()
    missing_source_types: tuple[str, ...] = ()
    unresolved_contradictions: tuple[UUID, ...] = ()
    recommended_actions: tuple[str, ...] = ()
    research_job_id: UUID | None = None
    status: str = "OPEN"
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    resolved_at: datetime | None = None


@dataclass(frozen=True)
class ReviewDecision:
    project_id: UUID
    reviewer_id: UUID
    target_type: str
    target_id: UUID
    decision: ReviewDecisionType
    reason: str
    old_status: str | None
    new_status: str | None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
