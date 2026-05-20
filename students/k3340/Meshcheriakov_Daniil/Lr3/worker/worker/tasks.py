from worker.celery_app import celery
from worker.db import save_skill
from worker.parser import fetch_and_extract


@celery.task(name="parser.parse_url", bind=True, max_retries=3, default_retry_delay=10)
def parse_url(self, url: str, category: str = "programming") -> dict:
    """Фоновая задача парсинга. Имя 'parser.parse_url' — api использует его
    в send_task. При сетевой ошибке Celery сделает до 3 ретраев."""
    try:
        title, description = fetch_and_extract(url)
    except Exception as exc:
        raise self.retry(exc=exc)

    created = save_skill(title, category, description)
    return {"title": title, "category": category, "created": created}


@celery.task(name="parser.ping")
def ping() -> str:
    """Периодическая задача-пингер (демонстрация beat_schedule)."""
    return "pong"
