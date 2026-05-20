from pydantic import BaseModel, HttpUrl


class ParseRequest(BaseModel):
    url: HttpUrl
    # programming / devops / databases / design / ...
    category: str = "programming"


class ParseResult(BaseModel):
    """Результат синхронного парсинга — пришёл от сервиса parser."""
    title: str
    category: str
    created: bool


class TaskQueued(BaseModel):
    """Ответ при постановке задачи в очередь Celery."""
    task_id: str
    status: str = "queued"


class TaskStatus(BaseModel):
    """Статус задачи Celery."""
    task_id: str
    status: str  # PENDING / STARTED / SUCCESS / FAILURE / RETRY / REVOKED
    result: dict | None = None
    error: str | None = None
