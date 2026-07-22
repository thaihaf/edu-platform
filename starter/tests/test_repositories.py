from uuid import uuid4
import pytest

pytest.importorskip("aiosqlite")
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from domain.entities import (
    Course,
    CourseVersion,
    ResearchProject,
    Source,
    SourceSnapshot,
    SourceType,
)
from infrastructure.database import Base
from infrastructure.repositories import (
    SqlAlchemyCourseRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemySourceRepository,
)


@pytest.mark.asyncio
async def test_sqlite_repository_round_trip_and_immutable_snapshots() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        projects, sources, courses = (
            SqlAlchemyProjectRepository(session),
            SqlAlchemySourceRepository(session),
            SqlAlchemyCourseRepository(session),
        )
        project = ResearchProject.create(
            workspace_id=uuid4(), title="Project", domain="IT", target="learner", created_by=uuid4()
        )
        await projects.add(project)
        source = Source.create(project_id=project.id, source_type=SourceType.PASTED_TEXT)
        await sources.add(source)
        snapshot = SourceSnapshot.create(
            source_id=source.id, content=b"immutable", content_hash="hash"
        )
        await sources.add_snapshot(snapshot)
        course = Course.create(project_id=project.id, title="Course")
        await courses.add(course)
        version = CourseVersion.draft(course_id=course.id, version_number=1, content={"a": 1})
        await courses.add_version(version)
        await session.commit()
        assert (await sources.list_snapshots(source.id))[0].content == b"immutable"
        published = version.publish()
        await courses.update_version(published)
        await session.commit()
        with pytest.raises(ValueError, match="immutable"):
            await courses.update_version(published)
    await engine.dispose()
