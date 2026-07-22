from __future__ import annotations

from apps.worker.worker.celery_app import celery_app
from apps.worker.worker.tasks import ping


def test_worker_is_configured_for_redis_and_idempotent_delivery() -> None:
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert ping.run() == "pong"
