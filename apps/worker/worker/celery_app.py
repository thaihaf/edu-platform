from __future__ import annotations

from celery import Celery

from packages.infrastructure.logging import configure_logging
from packages.infrastructure.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)

celery_app = Celery(
    "ai_course_worker",
    broker=str(settings.redis_url),
    backend=str(settings.celery_result_backend_url),
    include=["apps.worker.worker.tasks"],
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)
