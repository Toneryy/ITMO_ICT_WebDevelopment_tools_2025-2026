import os

from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery = Celery(
    "teamfinder_worker",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["worker.tasks"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Периодическое расписание (необязательное задание ЛР). Запускается, если
    # рядом стартует `celery -A worker.celery_app:celery beat`.
    beat_schedule={
        "ping-every-5-minutes": {
            "task": "parser.ping",
            "schedule": 300.0,
        },
    },
)
