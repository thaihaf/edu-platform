from celery import Celery

celery_app = Celery(
    "ai_course_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)
