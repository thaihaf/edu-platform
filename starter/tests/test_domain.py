from uuid import uuid4
import pytest
from domain.entities import CourseVersion, CourseVersionStatus, Source, SourceSnapshot, SourceType


def test_url_source_requires_url() -> None:
    with pytest.raises(ValueError, match="canonical_url"):
        Source.create(project_id=uuid4(), source_type=SourceType.URL)


def test_snapshot_is_immutable() -> None:
    snapshot = SourceSnapshot.create(source_id=uuid4(), content=b"content", content_hash="abc")
    with pytest.raises(AttributeError):
        snapshot.content = b"changed"  # type: ignore[misc]


def test_published_course_version_cannot_be_edited() -> None:
    published = CourseVersion.draft(
        course_id=uuid4(), version_number=1, content={"title": "v1"}
    ).publish()
    assert published.status is CourseVersionStatus.PUBLISHED
    with pytest.raises(ValueError, match="immutable"):
        published.edit({"title": "changed"})
