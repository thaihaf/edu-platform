"""In-memory test adapters and optional LangGraph workflow adapter."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from importlib.util import find_spec
from typing import Any, Protocol
from uuid import UUID, uuid4

from packages.domain.research import (
    CoverageReport,
    PlannedQuery,
    ResearchBrief,
    ResearchError,
    ResearchEvent,
    ResearchGap,
    ResearchJob,
    ResearchModel,
    ResearchObservation,
    ResearchPhase,
    ResearchResult,
    ResearchState,
    ResearchStatus,
)
from packages.domain.search import QueryFamily


class InMemoryResearchJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[UUID, ResearchJob] = {}
        self.keys: dict[str, UUID] = {}

    async def get(self, id: UUID) -> ResearchJob | None:
        return self.jobs.get(id)

    async def by_key(self, key: str) -> ResearchJob | None:
        return self.jobs.get(self.keys[key]) if key in self.keys else None

    async def save(self, job: ResearchJob) -> ResearchJob:
        self.jobs[job.id] = job
        self.keys[job.idempotency_key] = job.id
        return job


class InMemoryResearchCheckpointStore:
    def __init__(self) -> None:
        self.states: dict[UUID, ResearchState] = {}
        self.nodes: dict[UUID, list[str]] = {}
        self.terminal: set[UUID] = set()

    async def save_checkpoint(self, job_id: UUID, node: str, state: ResearchState) -> None:
        if state.workflow_version != "phase5.v1":
            raise ResearchError("RESEARCH_CHECKPOINT_INCOMPATIBLE", "Unsupported workflow version")
        # reject accidental source bodies in checkpoint payloads
        if "raw_content" in str(state.serializable()).lower():
            raise ResearchError(
                "RESEARCH_CHECKPOINT_INCOMPATIBLE", "Checkpoint contains source content"
            )
        self.states[job_id] = state
        self.nodes.setdefault(job_id, []).append(node)

    async def load_checkpoint(self, job_id: UUID, workflow_version: str) -> ResearchState:
        state = self.states.get(job_id)
        if not state:
            raise ResearchError("RESEARCH_CHECKPOINT_NOT_FOUND", "Checkpoint not found")
        if state.workflow_version != workflow_version:
            raise ResearchError(
                "RESEARCH_CHECKPOINT_INCOMPATIBLE", "Checkpoint workflow version differs"
            )
        return state

    async def list_checkpoints(self, job_id: UUID) -> list[str]:
        return self.nodes.get(job_id, [])

    async def mark_terminal(self, job_id: UUID) -> None:
        self.terminal.add(job_id)


class InMemoryResearchEventPublisher:
    def __init__(self) -> None:
        self.events: dict[UUID, list[ResearchEvent]] = {}

    async def publish(self, event: ResearchEvent) -> None:
        self.events.setdefault(event.research_job_id, []).append(event)


class InMemoryResearchArtifactRepository:
    def __init__(self) -> None:
        self.artifacts: dict[UUID, list[tuple[str, UUID, Any]]] = {}

    async def save(self, job_id: UUID, kind: str, payload: Any) -> UUID:
        for saved_kind, id, value in self.artifacts.get(job_id, []):
            if saved_kind == kind and value == payload:
                return id
        id = uuid4()
        self.artifacts.setdefault(job_id, []).append((kind, id, payload))
        return id

    async def list(self, job_id: UUID, kind: str | None = None) -> list[Any]:
        return [x[2] for x in self.artifacts.get(job_id, []) if kind is None or x[0] == kind]


class DeterministicResearchModel:
    """No network/model calls; suitable only for unit tests."""

    async def understand_goal(self, state: ResearchState) -> dict[str, Any]:
        return {"normalized_goal": " ".join(state.user_goal.split())}

    async def create_research_brief(self, state: ResearchState) -> ResearchBrief:
        goal = " ".join(state.user_goal.split())
        return ResearchBrief(
            goal,
            None,
            None,
            (),
            "research plan",
            state.learner_context,
            state.locale,
            state.time_range,
            (),
            (f"What is needed for {goal}?",),
            contradiction_searches=(f"conflicting reports about {goal}",),
            stop_criteria=("coverage threshold", "budget exhausted"),
        )

    async def generate_aliases(self, brief: ResearchBrief) -> dict[str, tuple[str, ...]]:
        return {"goal": (brief.normalized_goal,)}

    async def plan_queries(self, state: ResearchState) -> tuple[PlannedQuery, ...]:
        q = (
            state.research_brief.required_research_questions[0]
            if state.research_brief
            else state.user_goal
        )
        return (
            PlannedQuery(
                q,
                QueryFamily.DIRECT,
                "answer research question",
                "OFFICIAL",
                1,
                state.locale,
                state.time_range,
                parent_question=q,
                estimated_value=1,
            ),
            PlannedQuery(
                f"{q} filetype:pdf",
                QueryFamily.FILE_TYPE,
                "find documents",
                "DOCUMENT",
                2,
                state.locale,
                state.time_range,
                parent_question=q,
                estimated_value=0.8,
            ),
        )

    async def assist_source_selection(self, state: ResearchState) -> dict[UUID, float]:
        return {id: 1.0 for id in state.search_result_ids}

    async def extract_research_observations(
        self, state: ResearchState
    ) -> tuple[ResearchObservation, ...]:
        return ()

    async def analyze_gaps(self, state: ResearchState) -> tuple[ResearchGap, ...]:
        return ()

    async def plan_followup_queries(self, state: ResearchState) -> tuple[PlannedQuery, ...]:
        return ()

    async def assemble_research_result(self, state: ResearchState) -> ResearchResult:
        return ResearchResult(
            state.research_job_id,
            state.research_brief,
            state.executed_query_ids,
            state.selected_source_ids,
            state.coverage,
            state.gaps,
            state.extraction_artifact_ids,
            state.warnings,
            "minimum coverage reached",
            state.workflow_version,
        )


class ResearchSearchExecutor(Protocol):
    """Executes a planned query and returns IDs of discovered search results."""

    async def execute(self, query: PlannedQuery) -> tuple[UUID, ...]: ...


class DeterministicResearchSearchExecutor:
    """Test search adapter that records a real execution boundary without network I/O."""

    async def execute(self, query: PlannedQuery) -> tuple[UUID, ...]:
        return (uuid4(),)


class InMemoryResearchWorkflow:
    """Deterministic test runner for the application workflow contract, not production LangGraph."""

    nodes = (
        "understand_goal",
        "create_research_brief",
        "generate_aliases",
        "plan_queries",
        "execute_searches",
        "select_sources",
        "fetch_sources",
        "parse_sources",
        "extract_observations",
        "calculate_coverage",
        "analyze_gaps",
        "decide_followup",
        "plan_followup_queries",
        "finalize_research",
    )

    def __init__(
        self,
        jobs: InMemoryResearchJobRepository,
        checkpoints: InMemoryResearchCheckpointStore,
        model: ResearchModel | None = None,
        events: InMemoryResearchEventPublisher | None = None,
        artifacts: InMemoryResearchArtifactRepository | None = None,
        search_executor: ResearchSearchExecutor | None = None,
    ):
        self.jobs, self.checkpoints, self.model, self.events, self.artifacts = (
            jobs,
            checkpoints,
            model or DeterministicResearchModel(),
            events or InMemoryResearchEventPublisher(),
            artifacts or InMemoryResearchArtifactRepository(),
        )
        self.search_executor = search_executor or DeterministicResearchSearchExecutor()
        self._resume_locks: dict[UUID, asyncio.Lock] = {}

    async def start(self, job: ResearchJob, state: ResearchState) -> None:
        await self.checkpoints.save_checkpoint(job.id, "queued", state)
        await self.events.publish(ResearchEvent("job started", job.id, "Research queued", "queued"))

    async def get_state(self, job_id: UUID) -> ResearchState:
        return await self.checkpoints.load_checkpoint(job_id, "phase5.v1")

    async def get_progress(self, job_id: UUID) -> ResearchJob:
        job = await self.jobs.get(job_id)
        if not job:
            raise ResearchError("RESEARCH_JOB_NOT_FOUND", "Research job not found")
        return job

    async def _checkpoint(self, job: ResearchJob, state: ResearchState, node: str) -> None:
        job.current_node = node
        progress_node = node.removeprefix("failed:")
        job.progress_percent = min(
            99, (self.nodes.index(progress_node) + 1) * 100 // len(self.nodes)
        )
        await self.checkpoints.save_checkpoint(job.id, node, state)
        await self.jobs.save(job)

    def _lock_for(self, job_id: UUID) -> asyncio.Lock:
        """Return the process-local lease used by in-memory worker deliveries."""
        lock = self._resume_locks.get(job_id)
        if lock is None:
            lock = asyncio.Lock()
            self._resume_locks[job_id] = lock
        return lock

    async def _model_call(
        self, job: ResearchJob, state: ResearchState, call: Callable[[], Awaitable[Any]]
    ) -> Any:
        """Claim a model-call budget unit before the provider is invoked."""
        budget = state.budgets
        if budget.model_calls_used >= budget.model_call_budget:
            raise ResearchError("RESEARCH_BUDGET_EXHAUSTED", "Model-call budget exhausted")
        if budget.token_budget is not None and (budget.tokens_used or 0) >= budget.token_budget:
            raise ResearchError("RESEARCH_BUDGET_EXHAUSTED", "Token budget exhausted")
        if budget.cost_budget is not None and (budget.estimated_cost or 0) >= budget.cost_budget:
            raise ResearchError("RESEARCH_BUDGET_EXHAUSTED", "Cost budget exhausted")
        budget.model_calls_used += 1
        # state and job normally share this instance, but retain that invariant for
        # restored checkpoints which may have been deserialized independently.
        job.budgets.model_calls_used = budget.model_calls_used
        await self.jobs.save(job)
        return await call()

    async def _execute_queries(
        self, state: ResearchState, queries: tuple[PlannedQuery, ...]
    ) -> None:
        remaining = max(0, state.budgets.query_budget - state.budgets.queries_used)
        to_run = queries[:remaining]
        result_ids: list[UUID] = list(state.search_result_ids)
        executed = list(state.executed_query_ids)
        for query in to_run:
            # An ID only becomes executed after the search adapter has succeeded.
            result_ids.extend(await self.search_executor.execute(query))
            executed.append(query.id)
            state.budgets.queries_used += 1
        state.search_result_ids = tuple(result_ids)
        state.executed_query_ids = tuple(executed)

    async def _fail(
        self, job: ResearchJob, state: ResearchState, node: str, exc: Exception
    ) -> None:
        code = exc.code if isinstance(exc, ResearchError) else "RESEARCH_WORKFLOW_FAILED"
        message = exc.message if isinstance(exc, ResearchError) else str(exc)
        state.errors = (*state.errors, f"{code}: {message}")
        job.error_code, job.error_message = code, message
        if job.status is ResearchStatus.RUNNING:
            job.transition(ResearchStatus.FAILED)
        # Do not claim the failed node as complete: retry must re-run it.
        await self._checkpoint(job, state, f"failed:{node}")
        await self.events.publish(
            ResearchEvent("job failed", job.id, message, node, {"code": code})
        )

    async def _cancelled(self, job: ResearchJob) -> bool:
        if not job.cancellation_requested:
            return False
        if job.status is not ResearchStatus.CANCELLED:
            job.transition(ResearchStatus.CANCELLED)
            await self.jobs.save(job)
            await self.checkpoints.mark_terminal(job.id)
            await self.events.publish(
                ResearchEvent("job cancelled", job.id, "Cancellation requested")
            )
        return True

    async def resume(self, job_id: UUID) -> None:
        # The lease closes the checkpoint read/claim/write race for concurrent
        # deliveries in this in-memory adapter. Production stores must provide an
        # equivalent distributed lease or atomic checkpoint claim.
        async with self._lock_for(job_id):
            await self._resume_locked(job_id)

    async def _resume_locked(self, job_id: UUID) -> None:
        job = await self.get_progress(job_id)
        if job.status is ResearchStatus.COMPLETED:
            raise ResearchError("RESEARCH_ALREADY_COMPLETED", "Completed research cannot resume")
        if job.status is ResearchStatus.CANCELLED:
            raise ResearchError("RESEARCH_CANCELLED", "Cancelled research requires restart")
        if job.status in {ResearchStatus.PENDING, ResearchStatus.PAUSED, ResearchStatus.FAILED}:
            job.transition(ResearchStatus.RUNNING)
        state = await self.get_state(job_id)
        for node in self.nodes:
            if node in await self.checkpoints.list_checkpoints(job_id):
                continue
            if await self._cancelled(job):
                return
            await self.events.publish(ResearchEvent("phase started", job.id, node, node))
            try:
                if node == "understand_goal":
                    await self._model_call(job, state, lambda: self.model.understand_goal(state))
                    job.current_phase = ResearchPhase.SCOPING
                elif node == "create_research_brief":
                    state.research_brief = await self._model_call(
                        job, state, lambda: self.model.create_research_brief(state)
                    )
                    state.research_questions = state.research_brief.required_research_questions
                    job.current_phase = ResearchPhase.PLANNING
                elif node == "generate_aliases":
                    state.entity_aliases = await self._model_call(
                        job,
                        state,
                        lambda: self.model.generate_aliases(state.research_brief),  # type: ignore[arg-type]
                    )
                elif node == "plan_queries":
                    candidates = await self._model_call(
                        job, state, lambda: self.model.plan_queries(state)
                    )
                    unique = {q.fingerprint: q for q in candidates}
                    ordered = sorted(unique.values(), key=lambda q: (q.priority, q.fingerprint))
                    remaining = state.budgets.query_budget - state.budgets.queries_used
                    state.planned_queries = tuple(ordered[: max(0, remaining)])
                    job.current_phase = ResearchPhase.DISCOVERING
                elif node == "execute_searches":
                    await self._execute_queries(state, state.planned_queries)
                elif node == "select_sources":
                    job.current_phase = ResearchPhase.SELECTING
                elif node == "fetch_sources":
                    job.current_phase = ResearchPhase.FETCHING
                elif node == "parse_sources":
                    job.current_phase = ResearchPhase.PARSING
                    state.parsed_snapshot_ids = state.fetched_snapshot_ids
                elif node == "extract_observations":
                    job.current_phase = ResearchPhase.EXTRACTING
                    observations = await self._model_call(
                        job, state, lambda: self.model.extract_research_observations(state)
                    )
                    state.extraction_artifact_ids = tuple(
                        [
                            await self.artifacts.save(job.id, "observation", observation)
                            for observation in observations
                        ]
                    )
                elif node == "calculate_coverage":
                    state.coverage = CoverageReport(
                        1.0 if state.executed_query_ids else 0.0,
                        0.0,
                        0.0,
                        0.0,
                        len({q.family for q in state.planned_queries}) / 12,
                        False,
                        False,
                        False,
                        False,
                        marginal_information_gain=0.0,
                    )
                elif node == "analyze_gaps":
                    job.current_phase = ResearchPhase.GAP_ANALYSIS
                    state.gaps = await self._model_call(
                        job, state, lambda: self.model.analyze_gaps(state)
                    )
                elif node == "decide_followup":
                    job.current_phase = ResearchPhase.FOLLOWUP_RESEARCH
                elif node == "plan_followup_queries":
                    if (
                        state.gaps
                        and state.current_followup_round < state.budgets.max_followup_rounds
                    ):
                        candidates = await self._model_call(
                            job, state, lambda: self.model.plan_followup_queries(state)
                        )
                        known = {query.fingerprint for query in state.planned_queries}
                        followups = tuple(
                            query for query in candidates if query.fingerprint not in known
                        )
                        state.planned_queries = (*state.planned_queries, *followups)
                        state.current_followup_round += 1
                        job.followup_round = state.current_followup_round
                        await self._execute_queries(state, followups)
                elif node == "finalize_research":
                    job.current_phase = ResearchPhase.FINALIZING
                    result = await self._model_call(
                        job, state, lambda: self.model.assemble_research_result(state)
                    )
                    state.final_artifact_id = await self.artifacts.save(
                        job.id, "research_result", result
                    )
                    job.stop_reason = result.stop_reason
            except Exception as exc:
                await self._fail(job, state, node, exc)
                return
            await self._checkpoint(job, state, node)
            await self.events.publish(ResearchEvent("phase completed", job.id, node, node))
        job.current_phase = ResearchPhase.COMPLETED
        job.progress_percent = 100
        job.transition(ResearchStatus.COMPLETED)
        await self.jobs.save(job)
        await self.checkpoints.mark_terminal(job.id)
        await self.events.publish(ResearchEvent("job completed", job.id, "Research completed"))

    async def cancel(self, job_id: UUID) -> None:
        job = await self.get_progress(job_id)
        job.cancellation_requested = True
        await self._cancelled(job)

    async def retry(self, job_id: UUID) -> None:
        job = await self.get_progress(job_id)
        if job.status is not ResearchStatus.FAILED:
            raise ResearchError("INVALID_RESEARCH_TRANSITION", "Only failed research can retry")
        if job.retry_count >= job.max_retries:
            raise ResearchError("RESEARCH_BUDGET_EXHAUSTED", "Retry budget exhausted")
        job.retry_count += 1
        await self.jobs.save(job)
        await self.resume(job_id)


class LangGraphResearchWorkflow:
    """Production adapter boundary; live graph execution requires the optional runtime."""

    def __init__(self, *_: Any, **__: Any) -> None:
        if find_spec("langgraph") is None:
            raise ResearchError("WORKFLOW_PROVIDER_UNAVAILABLE", "LangGraph is not installed")
