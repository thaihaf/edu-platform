from __future__ import annotations

import asyncio

import httpx
import pytest
from fastapi import FastAPI

from apps.api.app.main import create_app
from packages.application.security import AuthorizationError, Principal, Role, require_role
from packages.infrastructure.production import Metrics, SlidingWindowRateLimiter
from packages.infrastructure.settings import Settings


class AvailableProbe:
    async def ping(self) -> None:
        return None


def request(app: FastAPI, path: str, headers: dict[str, str] | None = None) -> httpx.Response:
    async def run() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.get(path, headers=headers)

    return asyncio.run(run())


def test_rate_limiter_rejects_excess_requests_without_recording_address() -> None:
    app = create_app(
        Settings(rate_limit_requests=1, rate_limit_window_seconds=60),
        {"postgres": AvailableProbe()},
    )

    assert request(app, "/health/live").status_code == 200
    assert request(app, "/api/v1/workspaces/not-a-uuid").status_code != 429
    assert request(app, "/api/v1/workspaces/not-a-uuid").status_code == 429


def test_metrics_are_available_in_development_and_protected_in_production() -> None:
    development = create_app(Settings(app_env="development"), {"postgres": AvailableProbe()})
    assert "http_requests_total" in request(development, "/metrics").text

    production = create_app(
        Settings(
            app_env="production",
            metrics_token="test-token",
            otel_exporter_otlp_endpoint="https://otel",
        ),
        {"postgres": AvailableProbe()},
    )
    assert request(production, "/metrics").status_code == 404
    assert (
        request(production, "/metrics", {"Authorization": "Bearer test-token"}).status_code == 200
    )


def test_role_policy_requires_verified_principal_and_matching_role() -> None:
    admin = Principal(subject="operator-1", roles=frozenset({Role.ADMIN}))
    assert require_role(admin, Role.ADMIN) is admin
    with pytest.raises(AuthorizationError):
        require_role(None, Role.ADMIN)
    with pytest.raises(AuthorizationError):
        require_role(admin, Role.REVIEWER)


def test_metrics_render_deterministic_counters() -> None:
    metrics = Metrics()
    metrics.record_request("GET", 200, 0.01)
    assert 'http_requests_total{method="GET",status="200"} 1' in metrics.prometheus()


def test_sliding_window_expires_requests() -> None:
    now = [0.0]
    limiter = SlidingWindowRateLimiter(1, 10, clock=lambda: now[0])
    assert limiter.allow("client")
    assert not limiter.allow("client")
    now[0] = 10.0
    assert limiter.allow("client")


def test_production_configuration_requires_protected_metrics_and_telemetry() -> None:
    assert set(Settings(app_env="production").production_errors()) == {
        "METRICS_TOKEN",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    }
