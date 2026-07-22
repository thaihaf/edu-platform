"""Versioned structured-output prompt descriptors; templates stay outside use cases."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    schema_version: str = "1"


PROMPTS = {
    name: PromptTemplate(name, "v1")
    for name in (
        "curriculum-planning",
        "module-planning",
        "lesson-planning",
        "lesson-block-generation",
        "lesson-revision",
        "citation-selection",
        "draft-validation",
        "course-diff-summary",
    )
}
