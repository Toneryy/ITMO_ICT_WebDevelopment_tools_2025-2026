import httpx
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status

from app.celery_app import celery_app
from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.parser import ParseRequest, ParseResult, TaskQueued, TaskStatus

router = APIRouter(prefix="/parser", tags=["parser"])

# Имя задачи в worker. Должно совпадать с @celery.task(name=...) в worker/tasks.py.
PARSE_TASK_NAME = "parser.parse_url"


@router.post(
    "/sync",
    response_model=ParseResult,
    summary="Синхронный парсинг через сервис parser (HTTP)",
)
def parse_sync(
    payload: ParseRequest,
    _current_user: User = Depends(get_current_user),
) -> ParseResult:
    """Проксирует запрос в отдельный контейнер parser и ждёт результат."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{settings.parser_url}/parse",
                json={"url": str(payload.url), "category": payload.category},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Parser service responded with {exc.response.status_code}: {exc.response.text}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Parser service unreachable: {exc}",
        )
    return ParseResult(**response.json())


@router.post(
    "/async",
    response_model=TaskQueued,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Асинхронный парсинг — задача отправляется в очередь Celery",
)
def parse_async(
    payload: ParseRequest,
    _current_user: User = Depends(get_current_user),
) -> TaskQueued:
    """Кладёт задачу в Redis. Worker подхватит её и выполнит в фоне."""
    async_result = celery_app.send_task(
        PARSE_TASK_NAME,
        kwargs={"url": str(payload.url), "category": payload.category},
    )
    return TaskQueued(task_id=async_result.id)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatus,
    summary="Статус задачи парсинга по task_id",
)
def get_task_status(
    task_id: str,
    _current_user: User = Depends(get_current_user),
) -> TaskStatus:
    result = AsyncResult(task_id, app=celery_app)
    payload = TaskStatus(task_id=task_id, status=result.status)
    if result.successful():
        payload.result = result.result
    elif result.failed():
        payload.error = str(result.result)
    return payload
