from uuid import uuid4

import pytest

pytest.importorskip("aiosqlite")
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.main import create_app
from infrastructure.database import Base


def test_project_source_course_api() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    app = create_app(factory)
    with TestClient(app) as client:
        import asyncio

        asyncio.run(_create_schema(engine))
        response = client.post(
            "/projects",
            json={
                "workspace_id": str(uuid4()),
                "title": "Research",
                "domain": "IT",
                "target": "exam",
                "created_by": str(uuid4()),
            },
        )
        assert response.status_code == 201
        project_id = response.json()["id"]
        assert (
            client.post(f"/projects/{project_id}/sources", json={"source_type": "URL"}).status_code
            == 422
        )
        assert (
            client.post(
                f"/projects/{project_id}/sources",
                json={"source_type": "URL", "canonical_url": "https://example.test"},
            ).status_code
            == 201
        )
        course = client.post("/courses", json={"project_id": project_id, "title": "Course"}).json()
        version = client.post(
            f"/courses/{course['id']}/versions", json={"content": {"title": "draft"}}
        ).json()
        assert client.post(f"/course-versions/{version['id']}/publish").status_code == 200
        assert (
            client.put(f"/course-versions/{version['id']}", json={"content": {}}).status_code == 409
        )
    asyncio.run(engine.dispose())


async def _create_schema(engine: object) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)  # type: ignore[union-attr]
