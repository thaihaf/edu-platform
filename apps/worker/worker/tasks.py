from __future__ import annotations

from apps.worker.worker.celery_app import celery_app


@celery_app.task(name="platform.health.ping")  # type: ignore[untyped-decorator]
def ping() -> str:
    """Small operational task used to verify a worker can consume from Redis."""

    return "pong"
