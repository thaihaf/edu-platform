"""In-memory and optional DeepEval adapters for Phase 9."""

from __future__ import annotations
from collections import defaultdict
from statistics import mean
from packages.domain.evaluation import *


class InMemoryEvaluationRepository:
    def __init__(self) -> None:
        self.runs = {}
        self._keys = {}
        self.datasets = {}
        self.versions = {}
        self._cases = defaultdict(list)
        self.results = defaultdict(list)
        self._aggregates = defaultdict(list)
        self.policies = {}
        self.policy_versions = {}
        self.decisions = {}

    def by_key(self, p, k):
        return self._keys.get((p, k))

    def add_run(self, x):
        self.runs[x.id] = x
        self._keys[(x.project_id, x.idempotency_key)] = x

    def run(self, i):
        return self.runs.get(i)

    def add_dataset(self, x):
        self.datasets[x.id] = x

    def add_version(self, x):
        self.versions[x.id] = x

    def add_case(self, x):
        v = self.versions.get(x.dataset_version_id)
        if not v:
            raise EvaluationError("GOLDEN_DATASET_NOT_FOUND", "Dataset version not found")
        if v.status is not VersionStatus.DRAFT:
            raise EvaluationError(
                "GOLDEN_DATASET_VERSION_IMMUTABLE", "Published dataset version is immutable"
            )
        if any(c.case_key == x.case_key for c in self._cases[x.dataset_version_id]):
            raise EvaluationError("EVALUATION_CASE_INVALID", "Duplicate case key")
        self._cases[x.dataset_version_id].append(x)
        v.case_count += 1

    def cases(self, i):
        return tuple(self._cases[i])

    def publish_dataset(self, i):
        v = self.versions.get(i)
        if not v:
            raise EvaluationError("GOLDEN_DATASET_NOT_FOUND", "Dataset version not found")
        if not self._cases[i]:
            raise EvaluationError("GOLDEN_DATASET_VALIDATION_FAILED", "Dataset must contain cases")
        v.status = VersionStatus.PUBLISHED
        v.published_at = utcnow()
        return v

    def result(self, x):
        self.results[x.evaluation_run_id].append(x)

    def has_result(self, r, c, n, v):
        return any(
            x.evaluation_case_id == c and x.metric_name == n and x.metric_version == v
            for x in self.results[r]
        )

    def aggregate(self, r):
        if self._aggregates[r]:
            return tuple(self._aggregates[r])
        groups = defaultdict(list)
        for x in self.results[r]:
            groups[(x.metric_name, x.metric_version)].append(x)
        for (name, version), xs in groups.items():
            scores = [x.score for x in xs if x.score is not None]
            self._aggregates[r].append(
                EvaluationAggregate(
                    r,
                    name,
                    version,
                    len(xs),
                    sum(x.status is ResultStatus.PASS for x in xs),
                    sum(x.status is ResultStatus.FAIL for x in xs),
                    sum(x.status is ResultStatus.WARNING for x in xs),
                    sum(x.status is ResultStatus.ERROR for x in xs),
                    mean(scores) if scores else None,
                    min(scores) if scores else None,
                    max(scores) if scores else None,
                    {"p50": sorted(scores)[len(scores) // 2]} if scores else {},
                )
            )
        return tuple(self._aggregates[r])

    def aggregates(self, r):
        return tuple(self._aggregates[r])

    def add_policy(self, x):
        self.policies[x.id] = x

    def add_policy_version(self, x):
        self.policy_versions[x.id] = x

    def policy_version(self, i):
        return self.policy_versions.get(i)

    def add_decision(self, x):
        self.decisions[x.evaluation_run_id] = x

    def decision(self, i):
        return self.decisions.get(i)


class InMemoryEvaluationEvents:
    def __init__(self) -> None:
        self.events = defaultdict(list)

    def publish(self, run_id, event):
        self.events[run_id].append(event)


class DeterministicEvaluationProvider:
    provider_name = "deterministic"
    provider_version = "1"

    def supported_metrics(self):
        return ()

    def evaluate_case(self, case, metric, configuration):
        status, score, reasons, evidence = metric.evaluate(case, configuration)
        return EvaluationResult(
            UUID(int=0),
            case.artifact_type,
            metric.metric_name,
            metric.metric_version,
            status,
            score,
            configuration.get("threshold"),
            reasons,
            evidence,
            case.id,
        )

    def evaluate_batch(self, cases, metric, configuration):
        return tuple(self.evaluate_case(c, metric, configuration) for c in cases)


class DeepEvalProvider:
    provider_name = "deepeval"

    def __init__(self) -> None:
        try:
            import deepeval  # type: ignore[import-not-found]

            self._deepeval = deepeval
            self.provider_version = getattr(deepeval, "__version__", "unknown")
        except ImportError:
            self._deepeval = None
            self.provider_version = "unavailable"

    def supported_metrics(self):
        return ()

    def evaluate_case(self, case, metric, configuration):
        if self._deepeval is None:
            raise EvaluationError("EVALUATION_PROVIDER_UNAVAILABLE", "DeepEval is not installed")
        raise EvaluationError(
            "EVALUATION_PROVIDER_UNAVAILABLE", "DeepEval metric mapping is not configured"
        )

    def evaluate_batch(self, cases, metric, configuration):
        return tuple(self.evaluate_case(c, metric, configuration) for c in cases)
