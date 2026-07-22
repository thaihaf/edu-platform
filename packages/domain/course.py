"""Framework-neutral Phase 7 curriculum contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from packages.domain.models import InvalidStateTransitionError, utcnow


class GenerationStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class GenerationStage(StrEnum):
    VALIDATING_INPUT = "VALIDATING_INPUT"
    SELECTING_EVIDENCE = "SELECTING_EVIDENCE"
    PLANNING_CURRICULUM = "PLANNING_CURRICULUM"
    BUILDING_MODULES = "BUILDING_MODULES"
    BUILDING_LESSONS = "BUILDING_LESSONS"
    ATTACHING_CITATIONS = "ATTACHING_CITATIONS"
    VALIDATING_DRAFT = "VALIDATING_DRAFT"
    PERSISTING_VERSION = "PERSISTING_VERSION"
    COMPLETED = "COMPLETED"


class ConfidenceClass(StrEnum):
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    INFERRED = "INFERRED"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    HUMAN_AUTHORED = "HUMAN_AUTHORED"


class ContentBlockType(StrEnum):
    MARKDOWN = "MARKDOWN"
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    CALLOUT = "CALLOUT"
    DEFINITION = "DEFINITION"
    EXAMPLE = "EXAMPLE"
    CODE = "CODE"
    TABLE = "TABLE"
    DIAGRAM_SPEC = "DIAGRAM_SPEC"
    PROCEDURE = "PROCEDURE"
    SCENARIO = "SCENARIO"
    COMMON_MISTAKE = "COMMON_MISTAKE"
    INTERVIEW_TIP = "INTERVIEW_TIP"
    SOURCE_NOTE = "SOURCE_NOTE"
    SUMMARY = "SUMMARY"
    CHECKPOINT_PLACEHOLDER = "CHECKPOINT_PLACEHOLDER"


class CitationType(StrEnum):
    DIRECT = "DIRECT"
    SUPPORTING = "SUPPORTING"
    CONTEXT = "CONTEXT"
    CONTRADICTORY_NOTE = "CONTRADICTORY_NOTE"
    SOURCE_DISCLOSURE = "SOURCE_DISCLOSURE"


class BloomLevel(StrEnum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"


class Attribution(StrEnum):
    AI_GENERATED = "AI_GENERATED"
    HUMAN_AUTHORED = "HUMAN_AUTHORED"
    AI_REVISED = "AI_REVISED"
    HUMAN_REVISED = "HUMAN_REVISED"


class CourseError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(message)


@dataclass
class CourseGenerationJob:
    project_id: UUID
    idempotency_key: str
    target_outcome: str
    target_audience: str
    created_by: UUID
    locale: str = "en"
    course_id: UUID | None = None
    learner_profile: str | None = None
    time_budget: int | None = None
    module_limit: int | None = None
    lesson_limit: int | None = None
    status: GenerationStatus = GenerationStatus.PENDING
    current_stage: GenerationStage = GenerationStage.VALIDATING_INPUT
    progress_percent: int = 0
    policy_version: str = "course-policy-v1"
    prompt_version: str = "course-v1"
    request_fingerprint: str = ""
    id: UUID = field(default_factory=uuid4)
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def advance(self, stage: GenerationStage, progress: int) -> None:
        if self.status in {GenerationStatus.COMPLETED, GenerationStatus.CANCELLED}:
            raise InvalidStateTransitionError("Terminal generation job cannot advance")
        if list(GenerationStage).index(stage) < list(GenerationStage).index(self.current_stage):
            raise InvalidStateTransitionError("Generation stages cannot move backwards")
        self.status = GenerationStatus.RUNNING
        self.current_stage = stage
        self.progress_percent = progress
        self.started_at = self.started_at or utcnow()
        self.updated_at = utcnow()

    def complete(self) -> None:
        self.advance(GenerationStage.COMPLETED, 100)
        self.status = GenerationStatus.COMPLETED
        self.completed_at = utcnow()

    def fail(self, code: str, message: str) -> None:
        self.status = GenerationStatus.FAILED
        self.error_code = code
        self.error_message = message
        self.failed_at = utcnow()

    def cancel(self) -> None:
        self.status = GenerationStatus.CANCELLED
        self.cancelled_at = utcnow()


@dataclass
class CurriculumPlan:
    project_id: UUID
    generation_job_id: UUID
    title: str
    description: str
    target_outcome: str
    target_audience: str
    module_plan: list[dict[str, Any]]
    skill_coverage: list[UUID]
    evidence_coverage: list[UUID]
    warnings: list[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Module:
    course_version_id: UUID
    position: int
    title: str
    skill_ids: tuple[UUID, ...]
    description: str = ""
    estimated_duration_minutes: int = 30
    prerequisite_module_ids: tuple[UUID, ...] = ()
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Lesson:
    module_id: UUID
    position: int
    title: str
    summary: str
    learning_objective_ids: tuple[UUID, ...] = ()
    prerequisite_skill_ids: tuple[UUID, ...] = ()
    estimated_duration_minutes: int = 20
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class LearningObjective:
    objective_text: str
    measurable_verb: str
    bloom_level: BloomLevel
    linked_skill_ids: tuple[UUID, ...]
    linked_claim_ids: tuple[UUID, ...]
    lesson_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass
class ContentBlock:
    lesson_id: UUID
    position: int
    block_type: ContentBlockType
    content_json: dict[str, Any]
    confidence_class: ConfidenceClass
    linked_claim_ids: tuple[UUID, ...]
    linked_skill_ids: tuple[UUID, ...]
    evidence_link_ids: tuple[UUID, ...]
    prompt_version: str = "lesson-block-v1"
    attribution: Attribution = Attribution.AI_GENERATED
    locked: bool = False
    id: UUID = field(default_factory=uuid4)

    def edit(self, content: dict[str, Any], attribution: Attribution) -> None:
        if self.locked and attribution in {Attribution.AI_GENERATED, Attribution.AI_REVISED}:
            raise CourseError("PROTECTED_CONTENT_CONFLICT", "Content is locked from AI edits")
        self.content_json = content
        self.attribution = attribution


@dataclass(frozen=True)
class Citation:
    project_id: UUID
    course_version_id: UUID
    claim_id: UUID
    evidence_link_id: UUID
    source_id: UUID
    source_snapshot_id: UUID
    content_block_id: UUID | None = None
    citation_type: CitationType = CitationType.DIRECT
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class CourseVersionDiff:
    course_id: UUID
    from_version_id: UUID
    to_version_id: UUID
    diff_summary: str
    changed_modules: int
    changed_lessons: int
    changed_blocks: int
    id: UUID = field(default_factory=uuid4)
