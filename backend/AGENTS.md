# AGENTS.md — BScout Backend

Инструкции для AI-агентов, работающих над бэкендом BScout.

## Команды

```bash
uvicorn src.main:app --reload          # Dev server на :8000
alembic revision --autogenerate -m "msg"  # Создать миграцию
alembic upgrade head                   # Применить миграции
poetry run uvicorn src.main:app --reload  # Через Poetry
```

## Стек

- Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic
- PostgreSQL 16, Redis 7
- Pydantic v2, passlib (bcrypt), python-jose (JWT)
- Poetry для зависимостей

## Структура (модульная MVC)

```
src/
├── main.py                    # FastAPI app, CORS, подключение роутеров
├── config.py                  # pydantic-settings из .env
├── database.py                # async engine + sessionmaker + Base + get_db
└── modules/
    ├── shared/                # Общие зависимости
    │   └── deps.py            # get_current_user, get_current_admin
    ├── health/
    │   └── controller/
    │       └── health.py      # GET /api/health
    ├── auth/                  # Модуль аутентификации
    │   ├── model/
    │   │   └── user.py        # User, Subscription (SQLAlchemy)
    │   ├── schema/
    │   │   ├── auth.py        # RegisterRequest, LoginRequest, TokenResponse
    │   │   └── user.py        # UserResponse, SubscriptionResponse
    │   ├── service/
    │   │   └── auth.py        # bcrypt, JWT (create/decode), DB queries
    │   └── controller/
    │       └── auth.py        # POST /api/auth/register, /login, /refresh
    ├── users/                 # Модуль пользователей
    │   └── controller/
    │       └── users.py       # GET/PATCH /api/users/me, /subscription
    ├── admin/                 # Модуль админ-панели
    │   └── controller/        # (TODO)
    └── products/              # Модуль товаров и поиска
        └── controller/        # (TODO)
```

Каждый модуль содержит:
- **model/** — SQLAlchemy модели
- **schema/** — Pydantic v2 схемы request/response
- **service/** — бизнес-логика
- **controller/** — FastAPI роутеры

## Модели данных (ключевые)

- **User** — email, password_hash, full_name, phone, company, is_admin
- **Subscription** — user_id, plan (trial/basic/advanced), start/end_date, auto_renew
- **Store** — name, slug, website_url, logo_url
- **Product** — store_id, external_id, name, normalized_name, price, old_price, in_stock
- **PriceHistory** — product_id, price, recorded_at
- **SearchHistory** — user_id, query, filters, results_count

## API (текущие эндпоинты)

| Method | Path | Доступ |
|--------|------|--------|
| GET | /api/health | Public |
| POST | /api/auth/register | Public |
| POST | /api/auth/login | Public |
| POST | /api/auth/refresh | Public |
| GET | /api/users/me | Auth |
| PATCH | /api/users/me | Auth |
| GET | /api/users/me/subscription | Auth |
| POST | /api/users/me/subscription | Auth |

## Аутентификация

- JWT: access token (15 мин) + refresh token (30 дней)
- bcrypt (passlib) для хеширования паролей
- Bearer token через HTTPAuthorizationCredentials
- Public endpoints: /api/health, /api/auth/*, /api/stores, /api/categories

## Соглашения

- Все модели SQLAlchemy — async
- Все endpoint'ы — async def
- Миграции через Alembic (autogenerate)
- .env — в .gitignore, шаблон в .env.example
- snake_case в Python, camelCase в JSON (через Pydantic model_config)
- Никаких docstring'ов и комментариев в коде
