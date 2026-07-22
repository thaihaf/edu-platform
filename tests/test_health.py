from __future__ import annotations

import asyncio

import httpx
from fastapi import FastAPI

from apps.api.app.main import create_app
from packages.infrastructure.settings import Settings


class AvailableProbe:
    async def ping(self) -> None:
        return None


class UnavailableProbe:
    async def ping(self) -> None:
        raise ConnectionError("dependency unavailable")


def get(app: FastAPI, path: str, headers: dict[str, str] | None = None) -> httpx.Response:
    """Make an in-process request without coupling tests to Starlette's TestClient."""

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(path, headers=headers)

    return asyncio.run(request())


def test_live_health_is_always_available() -> None:
    app = create_app(Settings(), {"postgres": AvailableProbe(), "redis": AvailableProbe()})

    response = get(app, "/health/live", headers={"X-Trace-ID": "test-trace"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Trace-ID"] == "test-trace"


def test_ready_health_checks_all_required_dependencies() -> None:
    app = create_app(Settings(), {"postgres": AvailableProbe(), "redis": UnavailableProbe()})

    response = get(app, "/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "unavailable": ["redis"]}
    assert response.headers["X-Trace-ID"]


def test_ready_health_succeeds_when_dependencies_are_available() -> None:
    app = create_app(Settings(), {"postgres": AvailableProbe(), "redis": AvailableProbe()})

    response = get(app, "/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
