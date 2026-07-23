"""CI-safe golden JSONL validation and deterministic smoke evaluation."""

from __future__ import annotations
import json
from pathlib import Path
from packages.application.evaluation import EvaluationService
from packages.domain.evaluation import (
    ArtifactType,
    EvaluationCase,
    EvaluationRun,
    GoldenDataset,
    GoldenDatasetVersion,
)
from packages.infrastructure.evaluation import InMemoryEvaluationRepository

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> list[dict]:
    rows = []
    keys = set()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        key = row.get("case_key")
        if (
            not key
            or key in keys
            or "artifact_type" not in row
            or not isinstance(row.get("rubric"), dict)
        ):
            raise ValueError(f"invalid golden case in {path}: {key}")
        if any(word in json.dumps(row).casefold() for word in ("api_key", "password=", "secret=")):
            raise ValueError(f"secret-like value in {path}")
        keys.add(key)
        rows.append(row)
    return rows


def validate() -> None:
    for path in sorted((ROOT / "evals").glob("**/*.jsonl")):
        load(path)


def smoke() -> None:
    validate()
    repo = InMemoryEvaluationRepository()
    for path in sorted((ROOT / "evals").glob("**/*.jsonl")):
        for row in load(path):
            artifact = ArtifactType(row["artifact_type"])
            dataset = GoldenDataset(f"{path.stem}-{row['case_key']}", artifact, "en")
            version = GoldenDatasetVersion(dataset.id, 1, "fixture")
            repo.add_dataset(dataset)
            repo.add_version(version)
            repo.add_case(
                EvaluationCase(
                    version.id,
                    row["case_key"],
                    artifact,
                    row["input"],
                    row.get("expected"),
                    tuple(row.get("required_facts", [])),
                    tuple(row.get("forbidden_claims", [])),
                    tuple(row.get("required_sources", [])),
                    row["rubric"],
                )
            )
            metrics = (
                (("prompt_injection_resistance", "1"),)
                if artifact is ArtifactType.SOURCE
                else (("claim_groundedness", "1"),)
                if artifact in {ArtifactType.CLAIM, ArtifactType.RESEARCH_RESULT}
                else (("citation_coverage", "1"),)
                if artifact in {ArtifactType.COURSE_VERSION, ArtifactType.CONTENT_BLOCK}
                else (("single_best_answer", "1"),)
                if artifact is ArtifactType.QUESTION
                else (("context_precision", "1"),)
            )
            run = EvaluationRun(
                artifact,
                f"{path.stem}-{row['case_key']}",
                dataset_version_id=version.id,
                metric_set=metrics,
            )
            EvaluationService(repo).execute(EvaluationService(repo).start(run).id)


if __name__ == "__main__":
    smoke()
