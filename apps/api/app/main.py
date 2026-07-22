from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from packages.domain.ports import ReadinessProbe
from packages.infrastructure.logging import configure_logging
from packages.infrastructure.readiness import create_readiness_probes
from packages.infrastructure.settings import Settings, get_settings

logger = structlog.get_logger(__name__)


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Attach a caller-provided or generated trace ID to each HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = request.headers.get("X-Trace-ID") or str(uuid4())
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()


def create_app(
    settings: Settings | None = None,
    probes: dict[str, ReadinessProbe] | None = None,
) -> FastAPI:
    """Create the API with injected dependencies to keep health checks testable."""

    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)
    readiness_probes = probes if probes is not None else create_readiness_probes(runtime_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(
        title="AI Course Research Platform",
        version="0.1.0",
        description="Foundation API for the AI Research & Assessment Platform.",
        lifespan=lifespan,
    )
    app.add_middleware(TraceIdMiddleware)

    @app.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def ready() -> Response:
        unavailable: list[str] = []
        for name, probe in readiness_probes.items():
            try:
                await probe.ping()
            except Exception:
                unavailable.append(name)
                logger.warning("dependency_unavailable", dependency=name)

        if unavailable:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "unavailable": unavailable},
            )
        return JSONResponse(content={"status": "ok"})

    return app


app = create_app()
