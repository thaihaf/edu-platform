"""Small, vendor-neutral production hardening adapters.

These adapters deliberately avoid making an unverified request header an identity
source.  A deployment supplies a trusted identity adapter before it may enforce
RBAC at the HTTP boundary.
"""

from __future__ import annotations

import hashlib
import importlib.util
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)


class ErrorReporter(Protocol):
    def capture_exception(self, exc: Exception, *, trace_id: str) -> None: ...


class NullErrorReporter:
    def capture_exception(self, exc: Exception, *, trace_id: str) -> None:
        return None


@dataclass
class SentryCompatibleErrorReporter:
    """Logs a scrubbed error event at the Sentry-compatible integration boundary.

    Deployments may replace this adapter with the Sentry SDK transport; this local
    implementation never sends request bodies, authorization data, or secrets.
    """

    dsn: str

    def capture_exception(self, exc: Exception, *, trace_id: str) -> None:
        logger.error(
            "reported_exception",
            reporter="sentry-compatible",
            dsn_configured=bool(self.dsn),
            exception_type=type(exc).__name__,
            trace_id=trace_id,
        )


@dataclass
class Metrics:
    requests_total: dict[tuple[str, int], int] = field(default_factory=lambda: defaultdict(int))
    request_duration_seconds: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    rate_limit_rejections_total: int = 0

    def record_request(self, method: str, status_code: int, duration_seconds: float) -> None:
        self.requests_total[(method, status_code)] += 1
        self.request_duration_seconds[method].append(duration_seconds)

    def prometheus(self) -> str:
        lines = [
            "# HELP http_requests_total HTTP requests completed.",
            "# TYPE http_requests_total counter",
        ]
        for (method, status), value in sorted(self.requests_total.items()):
            lines.append(f'http_requests_total{{method="{method}",status="{status}"}} {value}')
        lines.extend(
            [
                "# HELP http_rate_limit_rejections_total Requests rejected by the rate limiter.",
                "# TYPE http_rate_limit_rejections_total counter",
                f"http_rate_limit_rejections_total {self.rate_limit_rejections_total}",
            ]
        )
        return "\n".join(lines) + "\n"


class SlidingWindowRateLimiter:
    """Process-local bounded fallback; use Redis-backed enforcement in production."""

    def __init__(
        self, limit: int, window_seconds: int, clock: Callable[[], float] = time.monotonic
    ):
        self.limit, self.window_seconds, self.clock = limit, window_seconds, clock
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self.clock()
        bucket = self._requests[key]
        while bucket and bucket[0] <= now - self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True


def client_key(client_host: str | None) -> str:
    """Avoid retaining raw client network identifiers in process memory/logs."""

    return hashlib.sha256((client_host or "unknown").encode()).hexdigest()[:24]


def configure_opentelemetry(service_name: str, endpoint: str) -> None:
    """Configure tracing only when the optional SDK is installed and endpoint is set."""

    if not endpoint:
        return
    if importlib.util.find_spec("opentelemetry") is None:
        logger.warning("opentelemetry_sdk_unavailable", service_name=service_name)
        return
    from opentelemetry import trace  # type: ignore[import-not-found]
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[import-not-found]
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource  # type: ignore[import-not-found]
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import-not-found]
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore[import-not-found]

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
