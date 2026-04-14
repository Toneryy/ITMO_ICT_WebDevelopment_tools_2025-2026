# Лабораторная работа №1 — REST API на FastAPI

**Студент:** Мещеряков Даниил  
**Группа:** K3340  

---

## Цель работы

Разработать REST API с использованием фреймворка FastAPI, реляционной базы данных PostgreSQL, ORM SQLAlchemy и системы миграций Alembic. Реализовать JWT-аутентификацию и CRUD-операции для нескольких сущностей.

---

## Предметная область

Платформа **TeamFinder** — сервис для поиска людей в команду. Пользователи могут:

- регистрироваться и управлять своим профилем с набором навыков;
- создавать проекты и указывать требуемые навыки;
- формировать команды внутри проектов и добавлять участников с указанием роли;
- искать пользователей по навыку и уровню владения.

---

## Стек технологий

| Компонент | Технология |
|-----------|------------|
| Фреймворк | FastAPI |
| ORM | SQLAlchemy 2.0 |
| База данных | PostgreSQL |
| Миграции | Alembic |
| Аутентификация | JWT (python-jose) |
| Хеширование паролей | passlib / bcrypt |
| Валидация | Pydantic v2 |
| Настройки | pydantic-settings |
| Сервер | Uvicorn |

---

## Структура проекта

```
Lr1/
├── app/
│   ├── main.py            # Точка входа, подключение роутеров
│   ├── config.py          # Настройки (DB URL, JWT secret)
│   ├── database.py        # Engine, SessionLocal, Base
│   ├── dependencies.py    # get_current_user (JWT dependency)
│   ├── models/
│   │   ├── user.py        # Модель User
│   │   ├── skill.py       # Модель Skill
│   │   ├── project.py     # Модель Project
│   │   ├── team.py        # Модель Team
│   │   └── associations.py # UserSkill, TeamMember, ProjectSkill
│   ├── schemas/           # Pydantic-схемы (входные/выходные DTO)
│   ├── routers/           # FastAPI-роутеры
│   └── services/
│       └── auth.py        # Хеширование, JWT, аутентификация
├── alembic/               # Миграции БД
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## Модели базы данных

### ER-диаграмма (описание связей)

```
User ──< UserSkill >── Skill
 |                       |
 |                    ProjectSkill
 |                       |
 └── owns ──> Project ──<─┘
                |
               Team ──< TeamMember >── User
```

### User

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | Идентификатор |
| email | String(255) unique | Email |
| username | String(100) unique | Логин |
| hashed_password | String(255) | Хеш пароля |
| full_name | String(255) | Полное имя |
| bio | Text | О себе |
| is_active | Boolean | Активен ли аккаунт |
| created_at | DateTime(tz) | Дата регистрации |

### Skill

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | Идентификатор |
| name | String(100) unique | Название навыка |
| category | String(100) | Категория (programming, design, devops…) |
| description | Text | Описание |

### Project

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | Идентификатор |
| title | String(255) | Название |
| description | Text | Описание |
| status | String(50) | open / in_progress / completed / cancelled |
| owner_id | FK → users.id | Владелец |
| created_at | DateTime(tz) | Дата создания |
| deadline | DateTime(tz) | Дедлайн |

### Team

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | Идентификатор |
| name | String(255) | Название |
| description | Text | Описание |
| project_id | FK → projects.id | Проект |
| created_at | DateTime(tz) | Дата создания |

### Ассоциативные таблицы

**UserSkill** (User ↔ Skill):

| Поле | Тип | Описание |
|------|-----|----------|
| user_id | FK PK | Пользователь |
| skill_id | FK PK | Навык |
| proficiency_level | String(50) | beginner / intermediate / expert |

**TeamMember** (Team ↔ User):

| Поле | Тип | Описание |
|------|-----|----------|
| user_id | FK PK | Пользователь |
| team_id | FK PK | Команда |
| role | String(100) | developer, designer, manager… |
| joined_at | DateTime(tz) | Дата вступления |

**ProjectSkill** (Project ↔ Skill):

| Поле | Тип | Описание |
|------|-----|----------|
| project_id | FK PK | Проект |
| skill_id | FK PK | Навык |
| required_level | String(50) | beginner / intermediate / expert |

---

## API Endpoints

### Аутентификация (`/auth`)

| Метод | Путь | Описание | Защита |
|-------|------|----------|--------|
| POST | `/auth/register` | Регистрация пользователя | — |
| POST | `/auth/login` | Получение JWT-токена | — |
| POST | `/auth/change-password` | Смена пароля | JWT |

### Пользователи (`/users`)

| Метод | Путь | Описание | Защита |
|-------|------|----------|--------|
| GET | `/users/` | Список всех пользователей | JWT |
| GET | `/users/me` | Текущий пользователь с навыками | JWT |
| PUT | `/users/me` | Обновление профиля | JWT |
| GET | `/users/search` | Поиск по навыку и уровню | JWT |
| GET | `/users/{user_id}` | Профиль пользователя | JWT |
| POST | `/users/me/skills` | Добавить навык в профиль | JWT |
| DELETE | `/users/me/skills/{skill_id}` | Удалить навык из профиля | JWT |

### Навыки (`/skills`)

| Метод | Путь | Описание | Защита |
|-------|------|----------|--------|
| GET | `/skills/` | Список навыков | JWT |
| POST | `/skills/` | Создать навык | JWT |
| GET | `/skills/{skill_id}` | Навык по ID | JWT |
| PUT | `/skills/{skill_id}` | Обновить навык | JWT |
| DELETE | `/skills/{skill_id}` | Удалить навык | JWT |

### Проекты (`/projects`)

| Метод | Путь | Описание | Защита |
|-------|------|----------|--------|
| GET | `/projects/` | Список проектов (фильтр по статусу) | — |
| POST | `/projects/` | Создать проект | JWT |
| GET | `/projects/search` | Поиск по навыку и статусу | — |
| GET | `/projects/{project_id}` | Детали проекта | — |
| PUT | `/projects/{project_id}` | Обновить проект (только владелец) | JWT |
| DELETE | `/projects/{project_id}` | Удалить проект (только владелец) | JWT |
| POST | `/projects/{project_id}/skills` | Добавить требуемый навык | JWT |
| DELETE | `/projects/{project_id}/skills/{skill_id}` | Убрать требуемый навык | JWT |

### Команды (`/teams`)

| Метод | Путь | Описание | Защита |
|-------|------|----------|--------|
| GET | `/teams/` | Список команд | — |
| POST | `/teams/` | Создать команду (только владелец проекта) | JWT |
| GET | `/teams/{team_id}` | Детали команды с участниками | — |
| PUT | `/teams/{team_id}` | Обновить команду | JWT |
| DELETE | `/teams/{team_id}` | Удалить команду | JWT |
| POST | `/teams/{team_id}/members` | Добавить участника | JWT |
| DELETE | `/teams/{team_id}/members/{user_id}` | Удалить участника | JWT |

---

## Аутентификация и авторизация

Используется схема **OAuth2 Bearer + JWT**.

1. Пользователь регистрируется через `POST /auth/register`.
2. Получает токен через `POST /auth/login` (форма `application/x-www-form-urlencoded`).
3. Токен передаётся в заголовке: `Authorization: Bearer <token>`.
4. Dependency `get_current_user` декодирует токен, проверяет подпись и возвращает объект пользователя.

Пароли хранятся в виде bcrypt-хеша. Время жизни токена — 60 минут (настраивается через `.env`).

---

## Миграции (Alembic)

Начальная миграция `cc07524daec5_initial` создаёт все таблицы в правильном порядке с учётом зависимостей внешних ключей:

```
skills → users → projects → user_skills → project_skills → teams → team_members
```

Все внешние ключи настроены с `ondelete="CASCADE"`.

**Команды:**

```bash
# Применить миграции
alembic upgrade head

# Создать новую миграцию
alembic revision --autogenerate -m "описание"

# Откатить последнюю миграцию
alembic downgrade -1
```

---

## Запуск проекта

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

Скопировать `.env.example` в `.env` и заполнить:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/teamfinder_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3. Применить миграции

```bash
alembic upgrade head
```

### 4. Запуск сервера

```bash
uvicorn app.main:app --reload
```

Или через `run_server.bat` на Windows.

### 5. Документация

После запуска доступна интерактивная документация:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Примеры запросов

### Регистрация

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "john",
    "password": "secret123",
    "full_name": "John Doe"
  }'
```

### Получение токена

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=john&password=secret123"
```

### Поиск пользователей по навыку

```bash
curl -X GET "http://localhost:8000/users/search?skill_id=1&proficiency_level=expert" \
  -H "Authorization: Bearer <token>"
```

### Создание проекта

```bash
curl -X POST http://localhost:8000/projects/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Project",
    "description": "Ищем разработчиков",
    "status": "open"
  }'
```

---

## Вывод

В ходе лабораторной работы была разработана REST API платформа TeamFinder на базе FastAPI. Реализованы:

- 5 групп эндпоинтов (auth, users, skills, projects, teams) с полным CRUD;
- JWT-аутентификация с bcrypt-хешированием паролей;
- реляционная схема БД с ассоциативными таблицами, несущими атрибуты связи (`proficiency_level`, `role`, `required_level`);
- миграции через Alembic;
- поиск пользователей по навыку/уровню и проектов по требуемому навыку/статусу;
- ролевой контроль доступа (только владелец проекта может изменять команды).
