---
name: backend-module
description: >
  Скаффолд нового модуля бэкенда BScout по паттерну модульного MVC
  (model / schema / service / controller) и регистрация роутера в main.py.
  Используй, когда просят добавить новую сущность, ресурс или группу
  эндпоинтов в FastAPI-бэкенд (например "добавь модуль отзывов",
  "новый эндпоинт для избранного", "CRUD для брендов").
argument-hint: "[module-name]"
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(poetry run *)
---

# Скаффолд backend-модуля: `$1`

Создай модуль `src/modules/$1/` строго по паттерну существующих модулей
(эталон — `src/modules/stores/` и `src/modules/products/`). Сначала прочитай
один из них целиком, чтобы скопировать стиль.

## Шаги

1. **Прочитать эталон**: `src/modules/stores/{model,schema,service,controller}/`.
2. **Создать дерево** `src/modules/$1/`:
   - `__init__.py` (пустой)
   - `model/__init__.py`, `model/$1.py` — SQLAlchemy-модель(и), наследующие `Base` из `src/database.py`.
   - `schema/__init__.py`, `schema/$1.py` — Pydantic v2 схемы request/response с `model_config` для camelCase.
   - `service/__init__.py`, `service/$1_service.py` — async-функции бизнес-логики (принимают `db: AsyncSession`).
   - `controller/__init__.py` — **экспортирует `$1_router`**; `controller/$1.py` — `APIRouter(prefix="/api/$1", tags=["$1"])`.
3. **Зарегистрировать роутер** в `src/main.py`: импорт `from src.modules.$1.controller import $1_router` и `app.include_router($1_router)`.
4. **Если добавлена модель/таблица** — зарегистрировать её импортом в `alembic/env.py` (иначе autogenerate её не увидит), затем сгенерировать миграцию: `poetry run alembic revision --autogenerate -m "add $1"` и применить `poetry run alembic upgrade head`.
5. **Проверить импорт**: `cd backend && poetry run python -c "import src.main"`.

## Обязательные конвенции (соблюдать)
- Всё `async` (модели, сессии, эндпоинты `async def`).
- snake_case в Python, camelCase в JSON (через `model_config`).
- **Без docstring и комментариев** в коде.
- Авторизация — `Depends(get_current_user)` / `get_current_admin` из `src/modules/shared/deps.py`.
- Если нужна новая таблица — помни: Alembic пока не настроен (см. `.claude/rules/backend.md`); не полагайся на `alembic upgrade` без настройки.

Не запускай `git commit`. По завершении покажи список созданных файлов и строку, добавленную в `main.py`.
