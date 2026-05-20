# Лабораторная работа №3 — Docker, источники данных и очереди

**Студент:** Мещеряков Даниил
**Группа:** K3340

---

## Цель работы

Научиться упаковывать FastAPI-приложение в Docker, интегрировать парсер данных с базой данных и вызывать его через HTTP и асинхронную очередь Celery + Redis.

---

## Архитектура

Композиция состоит из пяти сервисов, запускаемых одним `docker compose up`:

```
                  ┌──────────────────────────────────────────────────────┐
                  │                  docker compose                      │
                  │                                                      │
   клиент ──▶ api (8000)  ──HTTP──▶  parser (8001)  ──┐                  │
                  │   │                                ▼                 │
                  │   │                             db (PostgreSQL)      │
                  │   │                                ▲                 │
                  │   └──send_task──▶ redis (6379) ──▶ worker (Celery) ──┘
                  └──────────────────────────────────────────────────────┘
```

| Сервис | Образ / контекст | Назначение |
|--------|------------------|------------|
| **db** | `postgres:16-alpine` | Реляционная БД из Lr1 (TeamFinder). |
| **redis** | `redis:7-alpine` | Брокер сообщений и backend результатов Celery. |
| **api** | `./api` | FastAPI из Lr1 + роутер `/parser` (sync и async вызовы парсера). |
| **parser** | `./parser` | Отдельный FastAPI-сервис с эндпоинтом `POST /parse`. |
| **worker** | `./worker` | Celery-worker, обрабатывает задачи парсинга из очереди. |

Все сервисы живут в одной сети docker compose и обращаются друг к другу по hostname: `db`, `redis`, `parser`.

---

## Структура проекта

```
Lr3/
├── docker-compose.yml          # описание 5 сервисов
├── .env.example                # переменные окружения
├── README.md
│
├── api/                        # FastAPI из Lr1 + новые эндпоинты
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                # миграции, применяются при старте
│   └── app/
│       ├── celery_app.py       # клиент Celery (send_task, AsyncResult)
│       ├── routers/parser.py   # /parser/sync, /parser/async, /parser/tasks/{id}
│       └── ... (остальная часть Lr1: models, schemas, services, routers)
│
├── parser/                     # отдельный сервис парсера
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # POST /parse
│       ├── parser.py           # fetch + BeautifulSoup
│       └── db.py               # SQLAlchemy ORM (Skill)
│
└── worker/                     # Celery worker
    ├── Dockerfile
    ├── requirements.txt
    └── worker/
        ├── celery_app.py       # инициализация Celery + beat_schedule
        ├── tasks.py            # @celery.task parser.parse_url
        ├── parser.py           # та же логика парсинга
        └── db.py               # доступ к таблице skills
```

---

## Подзадача 1 — упаковка в Docker

### Dockerfile для FastAPI (api/Dockerfile)

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Аналогичный Dockerfile у `parser/` (порт 8001) и `worker/` (вместо uvicorn запускается `celery -A worker.celery_app:celery worker`).

### docker-compose.yml

Ключевые моменты:

- `db` и `redis` имеют `healthcheck`; `api` и `worker` стартуют только после `service_healthy`.
- `api` выполняет миграции при старте: `command: sh -c "alembic upgrade head && uvicorn ..."`.
- Все секреты и адреса хостов параметризованы через `.env`.
- Том `pg_data` сохраняет данные PostgreSQL между перезапусками.

```yaml
services:
  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d teamfinder_db"]
      interval: 5s
      retries: 10
    volumes: [pg_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  api:
    build: ./api
    environment:
      DATABASE_URL: postgresql+psycopg://postgres:superuser@db:5432/teamfinder_db
      PARSER_URL: http://parser:8001
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
      parser: { condition: service_started }
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

  parser:
    build: ./parser
    depends_on:
      db: { condition: service_healthy }

  worker:
    build: ./worker
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    command: celery -A worker.celery_app:celery worker --loglevel=info --concurrency=4
```

### Запуск

```bash
cp .env.example .env
docker compose up --build
```

После старта:

- Swagger основного API: <http://localhost:8000/docs>
- Swagger парсера: <http://localhost:8001/docs>

---

## Подзадача 2 — вызов парсера через HTTP

### Сервис parser

Отдельный FastAPI на порту 8001. Эндпоинт `POST /parse`:

```python
@app.post("/parse", response_model=ParseResponse)
def parse(payload: ParseRequest) -> ParseResponse:
    title, description = fetch_and_extract(str(payload.url))
    created = save_skill(title, payload.category, description)
    return ParseResponse(title=title, category=payload.category, created=created)
```

`fetch_and_extract` загружает HTML через `requests` и парсит BeautifulSoup-ом:

- `title` — текст первого `<h1>`;
- `description` — первый содержательный `<p>` из `div.mw-parser-output` (структура Wikipedia, как в Lr2).

`save_skill` пишет запись в таблицу `skills` (таблица из Lr1) с проверкой уникальности по имени.

### Эндпоинт-проксирующий в api

В основном API добавлен роутер `app/routers/parser.py`:

```python
@router.post("/sync", response_model=ParseResult)
def parse_sync(payload: ParseRequest,
               _current_user: User = Depends(get_current_user)) -> ParseResult:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{settings.parser_url}/parse",
            json={"url": str(payload.url), "category": payload.category},
        )
        response.raise_for_status()
    return ParseResult(**response.json())
```

`settings.parser_url` берётся из переменной `PARSER_URL` (`http://parser:8001`) — то есть api ходит в parser **по hostname сервиса** через внутреннюю сеть compose.

### Пример вызова

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=john&password=secret123" | jq -r .access_token)

curl -X POST http://localhost:8000/parser/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://en.wikipedia.org/wiki/Kubernetes","category":"devops"}'
# → {"title": "Kubernetes", "category": "devops", "created": true}
```

Запрос `api → parser → db` происходит синхронно; клиент блокируется до завершения парсинга.

---

## Подзадача 3 — асинхронный вызов через Celery + Redis

### Worker

`worker/worker/celery_app.py`:

```python
celery = Celery(
    "teamfinder_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    include=["worker.tasks"],
)
celery.conf.update(task_track_started=True, timezone="UTC", enable_utc=True)
```

`worker/worker/tasks.py`:

```python
@celery.task(name="parser.parse_url", bind=True, max_retries=3, default_retry_delay=10)
def parse_url(self, url: str, category: str = "programming") -> dict:
    try:
        title, description = fetch_and_extract(url)
    except Exception as exc:
        raise self.retry(exc=exc)
    created = save_skill(title, category, description)
    return {"title": title, "category": category, "created": created}
```

Запускается командой:

```
celery -A worker.celery_app:celery worker --loglevel=info --concurrency=4
```

`--concurrency=4` — четыре параллельных воркер-процесса в одном контейнере.

### Постановка задачи из api

В `api/app/celery_app.py` создаётся **клиент** Celery с тем же broker / backend:

```python
celery_app = Celery(
    "teamfinder_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
```

API не импортирует код таски — он шлёт её по имени:

```python
@router.post("/async", response_model=TaskQueued, status_code=202)
def parse_async(payload: ParseRequest,
                _current_user: User = Depends(get_current_user)) -> TaskQueued:
    async_result = celery_app.send_task(
        "parser.parse_url",
        kwargs={"url": str(payload.url), "category": payload.category},
    )
    return TaskQueued(task_id=async_result.id)
```

Эндпоинт возвращает `202 Accepted` сразу — клиент не ждёт окончания работы.

### Получение статуса

```python
@router.get("/tasks/{task_id}", response_model=TaskStatus)
def get_task_status(task_id: str,
                    _current_user: User = Depends(get_current_user)) -> TaskStatus:
    result = AsyncResult(task_id, app=celery_app)
    payload = TaskStatus(task_id=task_id, status=result.status)
    if result.successful():
        payload.result = result.result
    elif result.failed():
        payload.error = str(result.result)
    return payload
```

Возможные статусы: `PENDING`, `STARTED`, `SUCCESS`, `FAILURE`, `RETRY`, `REVOKED` — стандартные значения Celery.

### Пример

```bash
# поставить в очередь
curl -X POST http://localhost:8000/parser/async \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://en.wikipedia.org/wiki/Redis","category":"databases"}'
# → {"task_id": "a3b9c1...","status":"queued"}

# проверить статус
curl http://localhost:8000/parser/tasks/a3b9c1... \
  -H "Authorization: Bearer $TOKEN"
# → {"task_id":"a3b9c1...","status":"SUCCESS",
#    "result":{"title":"Redis","category":"databases","created":true}}
```

---

## Дополнительно — периодические задачи

В `worker/celery_app.py` настроен `beat_schedule` с демонстрационной задачей `parser.ping`, выполняющейся каждые 5 минут:

```python
celery.conf.update(
    beat_schedule={
        "ping-every-5-minutes": {
            "task": "parser.ping",
            "schedule": 300.0,
        },
    },
)
```

Для активации достаточно запустить рядом с воркером `celery beat`:

```
celery -A worker.celery_app:celery beat --loglevel=info
```

---

## Сводная таблица эндпоинтов парсера

| Метод | Путь | Описание | Защита |
|-------|------|----------|--------|
| POST | `/parser/sync` | Синхронный парсинг через HTTP в parser-сервис | JWT |
| POST | `/parser/async` | Постановка задачи парсинга в Celery-очередь | JWT |
| GET | `/parser/tasks/{task_id}` | Статус задачи Celery | JWT |
| POST | `/parse` (на 8001) | Прямой вызов парсера (внутренний интерфейс) | — |

---

## Проблемы и решения

| Проблема | Решение |
|----------|---------|
| Race condition: api стартует до того, как Postgres готов принимать соединения | `healthcheck` для `db`/`redis` + `depends_on: condition: service_healthy` |
| Миграции должны применяться один раз при первом запуске | `api.command: sh -c "alembic upgrade head && uvicorn ..."` — миграции идемпотентны (Alembic пропустит уже применённые) |
| Worker и parser пишут в ту же таблицу `skills`, что и api | Owner схемы — api (alembic). Worker и parser используют локальные ORM-модели, повторяющие структуру таблицы, без миграций |
| API не должен импортировать код воркера | Celery-клиент шлёт задачу по строковому имени `parser.parse_url`. Worker регистрирует это имя через `@celery.task(name=...)` |
| Сборка тяжёлая из-за `psycopg[binary]` и `bcrypt` | В Dockerfile установлен только `libpq5` рантайм; для разработки этого достаточно |

---

## Вывод

В ходе работы FastAPI-приложение из Lr1 и парсер из Lr2 были объединены в единую docker-compose композицию из пяти сервисов. Парсер выделен в отдельный контейнер и вызывается двумя способами:

- **синхронно** через HTTP (`api → parser`) — клиент ждёт результата;
- **асинхронно** через очередь Celery + Redis — клиент сразу получает `task_id` и опрашивает статус по нему.

Такое разделение демонстрирует базовый паттерн микросервисной архитектуры: ресурсоёмкая работа выносится из основного API в отдельные сервисы и в фоновую обработку, что позволяет масштабировать каждый компонент независимо и не блокировать обработку входящих запросов.
