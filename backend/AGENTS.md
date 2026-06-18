# AGENTS.md — BScout Backend

Инструкции для AI-агентов, работающих над бэкендом BScout.

## Команды

```bash
uvicorn src.main:app --reload     # Dev server на :8000
alembic revision --autogenerate -m "msg"  # Создать миграцию
alembic upgrade head              # Применить миграции
```

## Стек

- Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic
- PostgreSQL 16, Redis 7
- Pydantic v2 (schemas), python-dotenv / pydantic-settings

## Планируемая структура

```
src/
├── main.py           # FastAPI app, CORS, роутеры
├── config.py         # pydantic-settings из .env
├── database.py       # async engine + sessionmaker
├── models/           # SQLAlchemy модели
│   ├── user.py       # User, Subscription
│   ├── product.py    # Product, PriceHistory, Store
│   └── search.py     # SearchHistory, SavedSearch
├── schemas/          # Pydantic request/response
│   ├── user.py
│   ├── product.py
│   ├── auth.py
│   └── subscription.py
├── api/              # Роутеры
│   ├── health.py     # GET /api/health
│   ├── auth.py       # register, login, refresh, logout
│   ├── users.py      # profile, subscription
│   ├── products.py   # search, details, price-history
│   ├── stores.py     # stores list
│   └── admin.py      # admin endpoints
├── services/         # Бизнес-логика
│   ├── auth.py       # JWT, bcrypt
│   ├── search.py     # exact + fuzzy поиск
│   ├── subscription.py # лимиты, проверка
│   ├── parser.py     # управление парсерами
│   └── cache.py      # Redis кэш
├── parsers/          # Парсеры магазинов
│   ├── base.py       # ABC Parser
│   ├── tgssm.py
│   ├── profi.py
│   ├── liberty.py
│   ├── greenspark.py
│   └── divizion.py
└── utils/
    └── text.py       # нормализация, транслит
```

## Модели данных (ключевые)

- **User** — email, password_hash, full_name, phone, company, is_admin
- **Subscription** — user_id, plan (trial/basic/advanced), start/end_date, auto_renew
- **Store** — name, slug, website_url, logo_url
- **Product** — store_id, external_id, name, normalized_name, price, old_price, in_stock
- **PriceHistory** — product_id, price, recorded_at
- **SearchHistory** — user_id, query, filters, results_count

## API (планируемые эндпоинты)

| Method | Path | Доступ |
|--------|------|--------|
| POST | /api/auth/register | Public |
| POST | /api/auth/login | Public |
| POST | /api/auth/refresh | Public |
| POST | /api/auth/logout | Auth |
| GET | /api/users/me | Auth |
| PATCH | /api/users/me | Auth |
| GET | /api/users/me/subscription | Auth |
| POST | /api/users/me/subscription | Auth |
| GET | /api/products?q=... | Auth |
| GET | /api/stores | Public |
| GET | /api/categories | Public |
| GET/PATCH/DELETE | /api/admin/users | Admin |

## Аутентификация

- JWT: access token (15 мин) + refresh token (30 дней, httpOnly cookie)
- bcrypt (passlib) для хеширования паролей
- Проверка тарифа на поисковых маршрутах
- Public endpoints: /api/health, /api/auth/*, /api/stores, /api/categories

## Парсинг

- Базовый класс `Parser` (ABC): `parse_product()`, `search()`, `update_catalog()`
- Парсеры для 5 магазинов: ТГСМ, Профи, Либерти, Гринспарк, Дивизион
- Асинхронные (httpx / aiohttp)
- Расписание: каталог — ежедневно 03:00, цены — каждые 6ч / real-time

## Соглашения

- Все модели SQLAlchemy — async (selectinload, joinedload)
- Все endpoint'ы — async def
- Миграции через Alembic (autogenerate)
- .env — в .gitignore, шаблон в .env.example
- Pydantic v2 для валидации входа/выхода
- Redis: кэш поиска (TTL 5 мин), очередь задач (arq/RQ)
- Имена атрибутов — snake_case в Python, camelCase в JSON (через Pydantic)
