from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from packages.domain.models import (
    CourseVersion,
    CourseVersionStatus,
    ImmutableResourceError,
    ProjectStatus,
    ResearchProject,
    SourceSnapshot,
    Workspace,
)


def test_uuid_entities_and_snapshot_immutability() -> None:
    workspace = Workspace("example")
    snapshot = SourceSnapshot(uuid4(), 1, None, "hash")
    assert workspace.id.version == 4
    with pytest.raises((FrozenInstanceError, AttributeError)):
        snapshot.content_hash = "other"  # type: ignore[misc]


def test_project_and_course_transitions() -> None:
    project = ResearchProject(uuid4(), "title", "", "domain", "target", "en", 1, uuid4())
    project.update(status=ProjectStatus.ACTIVE)
    assert project.status is ProjectStatus.ACTIVE
    version = CourseVersion(uuid4(), 1, "t", "d", {}, uuid4())
    version.edit(title="changed")
    version.publish()
    assert version.status is CourseVersionStatus.PUBLISHED
    with pytest.raises(ImmutableResourceError):
        version.edit(title="no")
