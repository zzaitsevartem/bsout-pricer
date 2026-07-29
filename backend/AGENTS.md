# AGENTS.md — BScout Backend

Инструкции для AI-агентов, работающих над бэкендом BScout.

## Команды

```bash
uvicorn src.main:app --reload          # Dev server на :8000
alembic revision --autogenerate -m "msg"  # Создать миграцию
alembic upgrade head                   # Применить миграции
python src/seed.py                     # Наполнить БД тестовыми данными

# Тесты (отдельный venv, SQLite, без Docker)
/tmp/venv-bscout/bin/pytest -v         # Все тесты
/tmp/venv-bscout/bin/pytest -v -k "test_name"  # Конкретный тест
```

## Стек

- Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Alembic
- PostgreSQL 16, Redis 7
- Pydantic v2, passlib (bcrypt==4.0.1), python-jose (JWT)
- pytest + pytest-asyncio + aiosqlite (тесты)

## Структура (модульная MVC)

```
src/
├── main.py                    # FastAPI app, CORS, подключение роутеров
├── config.py                  # pydantic-settings из .env
├── database.py                # async engine + sessionmaker + Base + get_db
├── seed.py                    # Seed-скрипт (2 users, 5 stores: ТГСМ/Профи/Либерти/ГринСпарк/Дивизион, 5 категорий запчастей, 10 товаров)
└── modules/
    ├── shared/                # Общие зависимости
    │   └── deps.py            # get_current_user, get_current_admin, require_active_subscription
    ├── health/                # Health check
    │   └── controller/health.py
    ├── auth/                  # Аутентификация (регистрация, логин, JWT, logout)
    │   ├── model/user.py      # User, Subscription (SQLAlchemy)
    │   ├── schema/            # auth.py, user.py (Pydantic)
    │   ├── service/auth.py    # bcrypt, JWT, DB queries
    │   └── controller/auth.py # POST /api/auth/register, /login, /refresh, /logout
    ├── users/                 # Профиль пользователя
    │   └── controller/users.py # GET/PATCH /api/users/me, subscription
    ├── products/              # Товары, поиск, история цен
    │   ├── model/product.py   # Product, PriceHistory, Category
    │   ├── schema/product.py  # Pydantic response/request схемы
    │   ├── service/product_service.py  # search, фильтры, пагинация, сортировка
    │   └── controller/products.py  # GET /api/products, /{id}, /{id}/price-history
    ├── stores/                # Магазины
    │   ├── model/store.py     # Store
    │   ├── schema/store.py    # Pydantic схемы
    │   ├── service/store_service.py
    │   └── controller/stores.py  # GET/POST/PATCH /api/stores
    ├── categories/            # Категории
    │   ├── model/category.py  # Category
    │   ├── schema/category.py
    │   ├── service/category_service.py
    │   └── controller/categories.py  # GET/POST/PATCH /api/categories
    ├── admin/                 # Админ-панель
    │   └── controller/        # GET /api/admin/* (stats, users, parsers)
    ├── payment/               # Оплата
    │   └── controller/        # POST /api/payment/subscribe, /cancel
    ├── plans/                 # Тарифные планы
    │   ├── model/plan.py      # Plan (trial/basic/advanced)
    │   ├── schema/plan.py
    │   ├── service/plan_service.py
    │   └── controller/plans.py  # GET /api/plans
    └── parsers/               # Парсеры
        ├── base_parser.py     # BaseParser ABC + ParserManager
        └── controller/        # GET/POST /api/admin/parsers
```

Каждый модуль содержит:
- **model/** — SQLAlchemy модели
- **schema/** — Pydantic v2 схемы request/response
- **service/** — бизнес-логика
- **controller/** — FastAPI роутеры

## Модели данных

| Модель | Поля |
|--------|------|
| **User** | id, email, password_hash, full_name, phone, company, is_admin |
| **Магазины (seed)** | ТГСМ (tgssm), Профи (profi), Либерти (liberty), ГринСпарк (greenspark), Дивизион (divizion) |
| **Категории (seed)** | Дисплеи, Аккумуляторы, Стекло и корпуса, Шлейфы и разъёмы, Инструмент |
| **Subscription** | id, user_id, plan (trial/basic/advanced), start_date, end_date, auto_renew, is_active |
| **Plan** | id, slug, name, price, period, discount, featured, features (JSON), tooltips (JSON) |
| **Store** | id, name, slug, website_url, logo_url, is_active |
| **Store slugs** | `tgssm` (ТГСМ), `profi` (Профи), `liberty` (Либерти), `greenspark` (ГринСпарк), `divizion` (Дивизион) |
| **Category** | id, name, slug |
| **Product** | id, store_id, category_id, external_id, name, normalized_name, description, image_url, price, old_price, currency, in_stock, product_url, last_updated |
| **PriceHistory** | id, product_id, price, recorded_at |
| **SearchHistory** | id, user_id, query, filters (JSON), results_count, created_at |

## API (полный список)

### Публичные (7)
| Method | Path | 
|--------|------|
| GET | /api/health |
| POST | /api/auth/register |
| POST | /api/auth/login |
| POST | /api/auth/refresh |
| GET | /api/stores |
| GET | /api/categories |
| GET | /api/plans |

### Публичные с preview (3)
| Method | Path | Описание |
|--------|------|----------|
| GET | /api/products | Поиск (preview 3 товара без подписки, полный доступ с подпиской) |
| GET | /api/products/{id} | Детальная товара (публично) |
| GET | /api/stores | Список магазинов |

### Требуют аутентификации (10)
| Method | Path | Описание |
|--------|------|----------|
| POST | /api/auth/logout | Blacklist refresh token |
| GET | /api/users/me | Профиль |
| PATCH | /api/users/me | Обновление профиля |
| GET | /api/users/me/subscription | Текущая подписка |
| POST | /api/users/me/subscription | Создание/обновление подписки |
| GET | /api/search/history | История поиска |
| POST | /api/payment/subscribe | Оплата |
| POST | /api/payment/cancel | Отмена |
| GET | /api/admin/stats | Статистика (admin) |
| GET | /api/admin/users | Список пользователей (admin) |

### Требуют подписки (1)
| Method | Path | Описание |
|--------|------|----------|
| GET | /api/products/{id}/price-history | История цен (требует active subscription) |

### Требуют прав администратора (8)
| Method | Path |
|--------|------|
| POST | /api/stores | Создать магазин |
| PATCH | /api/stores/{id} | Обновить магазин |
| POST | /api/categories | Создать категорию |
| PATCH | /api/categories/{id} | Обновить категорию |
| POST | /api/admin/users/{id}/toggle-active | Блокировка |
| GET | /api/admin/parsers | Статус парсеров |
| POST | /api/admin/parsers/run | Запуск парсера |
| POST | /api/users/me/subscription | Изменить подписку (admin) |

## Параметры поиска /api/products

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| q | str | "" | Полнотекстовый поиск (name + normalized_name) |
| store | str | null | Фильтр по slug магазина |
| category | str | null | Фильтр по slug категории |
| min_price | float | null | Мин. цена |
| max_price | float | null | Макс. цена |
| in_stock | bool | null | Только в наличии |
| sort_by | str | "price_asc" | price_asc, price_desc, date |
| page | int | 1 | Номер страницы |
| per_page | int | 20 | Элементов на странице (max 100) |

## Аутентификация

- JWT: access token (15 мин) + refresh token (30 дней)
- bcrypt 4.0.1 (passlib) — совместимость: зафиксирована версия bcrypt
- Bearer token через HTTPAuthorizationCredentials / Swagger Authorize
- Refresh token черный список в Redis при logout
- SubscriptionGuard: эндпоинты /api/products требуют активной подписки

## Тестирование

```bash
# Быстрый запуск тестов (без Docker)
/tmp/venv-bscout/bin/pytest -v

# Тесты используют:
# - SQLite (aiosqlite) — не требует PostgreSQL
# - MockRedis — не требует Redis
# - Отдельный venv /tmp/venv-bscout/
```

## Соглашения

- Все модели SQLAlchemy — async
- Все endpoint'ы — async def
- Миграции через Alembic (autogenerate)
- .env — в .gitignore, шаблон в .env.example
- snake_case в Python, camelCase в JSON (через Pydantic model_config)
- Никаких docstring'ов и комментариев в коде
