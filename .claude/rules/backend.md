---
description: Конвенции бэкенда BScout (FastAPI + async SQLAlchemy). Авто-подгружается при правке backend-файлов.
paths: ["backend/**/*.py"]
---

# Правила бэкенда (FastAPI, модульный MVC)

## Структура модуля
Каждая фича — `src/modules/<name>/` с разбиением:
- `model/` — SQLAlchemy-модели (наследуют `Base` из `src/database.py`).
- `schema/` — Pydantic v2 схемы request/response.
- `service/` — бизнес-логика и запросы к БД.
- `controller/` — FastAPI-роутер; `controller/__init__.py` экспортирует `<name>_router`.
Новый модуль добавлять этим паттерном — используй скил `/backend-module`. Роутер регистрировать в `src/main.py` через `app.include_router(...)`.

## Обязательные правила
- **Всё async**: модели, сессии (`get_db`), эндпоинты (`async def`).
- **snake_case и в Python, и в JSON.** `alias_generator`/`populate_by_name` не настроены ни в одной схеме — API отдаёт `website_url`, `is_active`, `created_at`, и фронтовые Zod-схемы ждут того же. Не вводи camelCase в отдельном модуле: получится остров, ломающий фронт.
- **Никаких docstring и комментариев в коде** (конвенция проекта).
- Зависимость БД — `db: AsyncSession = Depends(get_db)`.
- Авторизация — `Depends(get_current_user)` / `get_current_admin` из `src/modules/shared/deps.py`.
- Публичные эндпоинты: `/api/health`, `/api/auth/*`, `/api/stores`, `/api/categories`.
- JWT: access 15 мин + refresh 30 дней; пароли — bcrypt через passlib.

## Миграции (Alembic — async/asyncpg, первая миграция применена)
- `alembic/env.py` берёт URL из `src.config.settings.database_url` и импортирует все модели. **Каждую новую модель добавляй импортом в `alembic/env.py`**, иначе autogenerate её пропустит.
- Креды БД НЕ хранятся в `alembic.ini` (ставятся в рантайме) — не хардкодь их туда.
- Запускать через venv: `python -m alembic ...` (не `poetry`, poetry не установлен). Рабочий цикл из `backend/`:
  - `python -m alembic revision --autogenerate -m "описание"`
  - `python -m alembic upgrade head`
  - База уже под `fb0762d20565` (initial schema, 7 таблиц).
- Конфиг — `Settings` (pydantic-settings, `extra="ignore"`) из `.env`; шаблон в `.env.example`. Порт БД — `POSTGRES_PORT=5434` (см. `backend/.env`). Реальный `.env` не читать (заблокировано хуком protect-secrets).

## Форматирование
- `ruff` в dev-зависимостях (`pyproject.toml`, секция `[tool.ruff]`: E/W/F/I, line-length 100, `alembic/` исключён, `__init__.py` игнорит F401).
- Хук `backend-format` после правок прогоняет `ruff format` + `ruff check --fix` по изменённому файлу.
