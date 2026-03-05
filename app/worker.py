from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery("fastapi_marketplace")
celery_app.conf.update(
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
)
celery_app.autodiscover_tasks(["app.tasks"])
