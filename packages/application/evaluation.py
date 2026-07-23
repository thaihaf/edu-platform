"""Provider-neutral evaluation orchestration and deterministic safety metrics."""

from __future__ import annotations
from collections import defaultdict
from dataclasses import replace
from typing import Any
from packages.domain.evaluation import *


class MetricRegistry:
    def __init__(self) -> None:
        self._metrics: dict[tuple[str, str], DeterministicMetric] = {}
        self._definitions: dict[tuple[str, str], MetricDefinition] = {}

    def register(self, definition: MetricDefinition, metric: DeterministicMetric) -> None:
        key = (definition.name, definition.version)
        if key in self._metrics:
            raise EvaluationError(
                "EVALUATION_METRIC_VERSION_CONFLICT", "Metric name/version already registered"
            )
        if key != (metric.metric_name, metric.metric_version):
            raise EvaluationError(
                "EVALUATION_INPUT_INVALID", "Metric definition and implementation differ"
            )
        self._metrics[key], self._definitions[key] = metric, definition

    def resolve(self, name: str, version: str, artifact: ArtifactType) -> DeterministicMetric:
        metric = self._metrics.get((name, version))
        if not metric:
            raise EvaluationError(
                "EVALUATION_METRIC_NOT_FOUND", f"Metric {name}@{version} not found"
            )
        if artifact not in metric.supported_artifact_types:
            raise EvaluationError(
                "EVALUATION_INPUT_INVALID", "Metric incompatible with artifact type"
            )
        return metric

    def definitions(self) -> tuple[MetricDefinition, ...]:
        return tuple(self._definitions.values())


class FieldMetric:
    def __init__(
        self,
        name: str,
        types: tuple[ArtifactType, ...],
        field: str,
        *,
        inverse: bool = False,
        warning: bool = False,
    ) -> None:
        (
            self.metric_name,
            self.metric_version,
            self.supported_artifact_types,
            self.field,
            self.inverse,
            self.warning,
        ) = name, "1", types, field, inverse, warning

    def evaluate(
        self, case: EvaluationCase, configuration: dict[str, Any]
    ) -> tuple[ResultStatus, float | None, tuple[str, ...], dict[str, Any]]:
        value = case.input_json.get(self.field)
        score = float(value) if isinstance(value, (int, float)) else 1.0 if bool(value) else 0.0
        if self.inverse:
            score = 1 - score
        threshold = float(configuration.get("threshold", 1))
        status = (
            ResultStatus.PASS
            if score >= threshold
            else (ResultStatus.WARNING if self.warning else ResultStatus.FAIL)
        )
        return (
            status,
            score,
            (f"{self.field}={score}",),
            {"field": self.field, "configuration_hash": config_hash(configuration)},
        )


class SafetyMetric(FieldMetric):
    def evaluate(
        self, case: EvaluationCase, configuration: dict[str, Any]
    ) -> tuple[ResultStatus, float | None, tuple[str, ...], dict[str, Any]]:
        text = " ".join(str(x) for x in case.input_json.values()).casefold()
        if self.metric_name == "prompt_injection_resistance":
            injected = any(
                x in text
                for x in (
                    "give this a perfect score",
                    "ignore the rubric",
                    "mark as grounded",
                    "skip the failing metric",
                    "publish despite failure",
                )
            )
            return (
                ResultStatus.PASS,
                1.0,
                ("untrusted instructions treated as data",),
                {"injection_detected": injected},
            )
        if self.metric_name in {"claim_groundedness", "grounding", "reported_evidence_validity"}:
            supported = bool(case.input_json.get("evidence") or case.input_json.get("citations"))
            if self.metric_name == "reported_evidence_validity":
                supported = supported and bool(case.input_json.get("reported_origin"))
            return (
                (ResultStatus.PASS if supported else ResultStatus.FAIL),
                float(supported),
                ("direct evidence required",),
                {"citation_count": len(case.input_json.get("citations", []))},
            )
        if self.metric_name == "single_best_answer":
            count = sum(
                bool(x.get("is_correct"))
                for x in case.input_json.get("options", [])
                if isinstance(x, dict)
            )
            return (
                (ResultStatus.PASS if count == 1 else ResultStatus.FAIL),
                float(count == 1),
                ("exactly one correct option required",),
                {"correct_option_count": count},
            )
        if self.metric_name == "non_choice_answer":
            answer = case.input_json.get("answer") or case.input_json.get("rubric")
            return (
                (ResultStatus.PASS if bool(answer) else ResultStatus.FAIL),
                float(bool(answer)),
                ("non-choice answer or rubric required",),
                {},
            )
        if self.metric_name == "citation_coverage":
            factual = case.input_json.get("factual_blocks", [])
            cited = [b for b in factual if isinstance(b, dict) and b.get("citation")]
            score = 1.0 if not factual else len(cited) / len(factual)
            return (
                (ResultStatus.PASS if score == 1 else ResultStatus.FAIL),
                score,
                ("factual blocks require citations",),
                {},
            )
        return super().evaluate(case, configuration)


def default_registry() -> MetricRegistry:
    registry = MetricRegistry()
    all_types = tuple(ArtifactType)
    safety = {
        "prompt_injection_resistance": all_types,
        "claim_groundedness": (ArtifactType.CLAIM, ArtifactType.RESEARCH_RESULT),
        "grounding": (ArtifactType.QUESTION,),
        "reported_evidence_validity": (ArtifactType.QUESTION,),
        "single_best_answer": (ArtifactType.QUESTION,),
        "non_choice_answer": (ArtifactType.QUESTION,),
        "citation_coverage": (
            ArtifactType.COURSE_VERSION,
            ArtifactType.LESSON,
            ArtifactType.CONTENT_BLOCK,
        ),
    }
    fields = {
        "source_diversity": "distinct_clusters",
        "temporal_coverage": "temporal_coverage",
        "contradiction_search_coverage": "contradiction_coverage",
        "context_precision": "precision",
        "context_recall": "recall",
        "required_source_recall": "required_source_recall",
        "duplicate_result_rate": "duplicate_rate",
        "rank_stability": "rank_stability",
        "prerequisite_consistency": "prerequisites_valid",
        "published_version_immutability": "immutable",
        "ambiguity": "unambiguous",
        "publication_eligibility": "eligible",
        "evidence_span_validity": "span_valid",
        "confidence_reproducibility": "confidence_reproducible",
    }
    for name, types in safety.items():
        registry.register(
            MetricDefinition(name, "1", name, types), SafetyMetric(name, types, "evidence")
        )
    for name, field in fields.items():
        types = (
            all_types
            if name
            in {
                "source_diversity",
                "temporal_coverage",
                "contradiction_search_coverage",
                "prompt_injection_resistance",
            }
            else (
                {
                    "ambiguity": (ArtifactType.QUESTION,),
                    "publication_eligibility": (ArtifactType.QUESTION,),
                }.get(name, all_types)
            )
        )
        registry.register(
            MetricDefinition(name, "1", name, types),
            FieldMetric(
                name,
                types,
                field,
                inverse=name == "duplicate_result_rate",
                warning=name == "contradiction_search_coverage",
            ),
        )
    return registry


class EvaluationService:
    def __init__(
        self, repo: Any, registry: MetricRegistry | None = None, events: Any = None
    ) -> None:
        self.repo, self.registry, self.events = repo, registry or default_registry(), events

    def start(self, run: EvaluationRun) -> EvaluationRun:
        old = self.repo.by_key(run.project_id, run.idempotency_key)
        if old:
            if old.payload_hash() != run.payload_hash():
                raise EvaluationError("IDEMPOTENCY_CONFLICT", "Idempotency key payload differs")
            return old
        self.repo.add_run(run)
        self._event(run, "run started")
        return run

    def execute(self, run_id: Any) -> EvaluationRun:
        run = self.repo.run(run_id)
        if not run:
            raise EvaluationError("EVALUATION_RUN_NOT_FOUND", "Evaluation run not found")
        if run.status is RunStatus.CANCELLED:
            raise EvaluationError("EVALUATION_CANCELLED", "Evaluation run cancelled")
        if run.status is RunStatus.COMPLETED:
            return run
        cases = self.repo.cases(run.dataset_version_id)
        run.status = RunStatus.RUNNING
        run.current_stage = RunStage.RUNNING_DETERMINISTIC_METRICS
        run.total_cases = len(cases)
        self._event(run, "case started")
        for case in cases:
            if run.status is RunStatus.CANCELLED:
                return run
            for name, version in run.metric_set:
                if self.repo.has_result(run.id, case.id, name, version):
                    continue
                metric = self.registry.resolve(name, version, case.artifact_type)
                status, score, reasons, evidence = metric.evaluate(case, run.provider_config)
                self.repo.result(
                    EvaluationResult(
                        run.id,
                        case.artifact_type,
                        name,
                        version,
                        status,
                        score,
                        run.provider_config.get("threshold"),
                        reasons,
                        evidence,
                        case.id,
                    )
                )
                self._event(run, "metric completed")
            run.completed_cases += 1
        run.current_stage = RunStage.AGGREGATING
        self.repo.aggregate(run.id)
        run.current_stage = RunStage.APPLYING_QUALITY_GATES
        if run.quality_gate_policy_id:
            self.gate(run.id, run.quality_gate_policy_id)
        run.status = RunStatus.COMPLETED
        run.current_stage = RunStage.COMPLETED
        run.progress_percent = 100
        self._event(run, "run completed")
        return run

    def cancel(self, run_id: Any) -> EvaluationRun:
        run = self.repo.run(run_id)
        if not run:
            raise EvaluationError("EVALUATION_RUN_NOT_FOUND", "Evaluation run not found")
        run.status = RunStatus.CANCELLED
        run.cancelled_at = utcnow()
        self._event(run, "run cancelled")
        return run

    def gate(self, run_id: Any, version_id: Any) -> QualityGateDecision:
        existing = self.repo.decision(run_id)
        if existing:
            return existing
        policy = self.repo.policy_version(version_id)
        if not policy:
            raise EvaluationError("QUALITY_GATE_POLICY_NOT_FOUND", "Policy version not found")
        aggregates = {(a.metric_name, a.metric_version): a for a in self.repo.aggregates(run_id)}
        failures = []
        warnings = []
        for rule in policy.rules_json:
            key = (rule["metric_name"], rule.get("metric_version", "1"))
            a = aggregates.get(key)
            reason = rule["metric_name"]
            failed = (
                not a
                or (
                    rule.get("minimum_score") is not None
                    and (a.average_score is None or a.average_score < rule["minimum_score"])
                )
                or (a and a.fail_count > rule.get("maximum_failure_count", 0))
            )
            if failed:
                (failures if rule.get("hard", True) else warnings).append(reason)
        status = (
            GateStatus.FAILED
            if failures
            else GateStatus.PASSED_WITH_WARNINGS
            if warnings
            else GateStatus.PASSED
        )
        decision = QualityGateDecision(
            run_id,
            version_id,
            status,
            tuple(failures),
            tuple(warnings),
            "Deterministic gate evaluation",
        )
        self.repo.add_decision(decision)
        self._event(self.repo.run(run_id), "gate failed" if failures else "gate passed")
        return decision

    def compare(self, current: Any, baseline: Any, noise: float = 0.01) -> RegressionComparison:
        now = {(x.metric_name, x.metric_version): x for x in self.repo.aggregates(current)}
        before = {(x.metric_name, x.metric_version): x for x in self.repo.aggregates(baseline)}
        deltas = {}
        regressions = []
        improvements = []
        for key, a in now.items():
            old = before.get(key)
            if not old:
                continue
            delta = (a.average_score or 0) - (old.average_score or 0)
            label = "@".join(key)
            deltas[label] = delta
            if delta < -noise:
                regressions.append(label)
            elif delta > noise:
                improvements.append(label)
        return RegressionComparison(
            current,
            baseline,
            deltas,
            tuple(regressions),
            tuple(improvements),
            GateStatus.FAILED if regressions else GateStatus.PASSED,
        )

    def _event(self, run: EvaluationRun | None, event: str) -> None:
        if run and self.events:
            self.events.publish(run.id, event)
