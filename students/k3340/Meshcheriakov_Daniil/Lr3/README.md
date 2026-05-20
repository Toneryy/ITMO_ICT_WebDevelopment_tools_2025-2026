# Lr3 — Docker, источники данных, очереди

Композиция из 5 сервисов:

- **db** — PostgreSQL 16 (база TeamFinder из Lr1).
- **redis** — брокер сообщений и backend результатов Celery.
- **api** — основное FastAPI приложение (Lr1) + роутер `/parser` для синхронного и асинхронного вызова парсера.
- **parser** — отдельный FastAPI сервис с эндпоинтом `POST /parse`, парсит страницы и пишет в таблицу `skills`.
- **worker** — Celery worker, обрабатывает задачи парсинга из очереди.

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

После старта:

- Swagger основного API: <http://localhost:8000/docs>
- Swagger парсера: <http://localhost:8001/docs>

Alembic-миграции применяются автоматически при старте `api`.

## Использование эндпоинтов парсинга

Все эндпоинты требуют JWT. Сначала зарегистрируйся и залогинься через `/auth/register` и `/auth/login`.

### Синхронный вызов (подзадача 2)

```bash
curl -X POST http://localhost:8000/parser/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://en.wikipedia.org/wiki/Kubernetes","category":"devops"}'
```

`api` проксирует запрос в сервис `parser` по HTTP, ждёт ответа, возвращает результат.

### Асинхронный через Celery (подзадача 3)

```bash
# поставить задачу в очередь
curl -X POST http://localhost:8000/parser/async \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://en.wikipedia.org/wiki/Redis","category":"databases"}'
# → {"task_id": "..."}

# проверить статус
curl http://localhost:8000/parser/tasks/<task_id> \
  -H "Authorization: Bearer $TOKEN"
```

## Структура

```
Lr3/
├── docker-compose.yml
├── .env.example
├── api/         # FastAPI из Lr1 + роутер /parser
├── parser/      # отдельный FastAPI сервис парсера
└── worker/      # Celery worker
```
