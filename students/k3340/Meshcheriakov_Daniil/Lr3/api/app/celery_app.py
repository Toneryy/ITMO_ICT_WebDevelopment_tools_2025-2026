from celery import Celery

from app.config import settings

# Клиент Celery в api-сервисе. Сам worker живёт в отдельном контейнере;
# api только ставит задачи в очередь и запрашивает их статус по AsyncResult.
celery_app = Celery(
    "teamfinder_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
