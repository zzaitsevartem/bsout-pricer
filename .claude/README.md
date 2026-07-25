# .claude/ — конфигурация Claude Code для BScout

Единый индекс правил, скилов, хуков и MCP-подключений проекта. Формат — по
актуальному стандарту Claude Code (проектный scope, коммитится в репо).

> ⚠️ **Запускать `claude` из `bsout-pricer/`** (не из внешнего каталога `bscount/`).
> `bsout-pricer/` — корень проекта: отсюда резолвятся `.mcp.json`, `.claude/`,
> `${CLAUDE_PROJECT_DIR}` в хуках и `!`-команды в скилах.

## Что где лежит

| Путь | Назначение |
|------|------------|
| `.mcp.json` (корень проекта) | 4 MCP-сервера (см. ниже) |
| `.claude/settings.json` | permissions + hooks — **коммитится**, общий для команды |
| `.claude/settings.local.json` | личные оверрайды — **в .gitignore**; шаблон: `settings.local.json.example` |
| `.claude/rules/*.md` | path-scoped правила, авто-подгрузка при правке файлов |
| `.claude/skills/*/SKILL.md` | скилы (вызов `/name` или авто-триггер по описанию) |
| `.claude/hooks/*.sh` | скрипты хуков |
| `CLAUDE.md` (в `bscount/`, родительский) | общий обзор архитектуры (подхватывается как parent) |

## MCP-серверы (`.mcp.json`)

| Сервер | Пакет | Назначение | Заметки |
|--------|-------|------------|---------|
| `postgres` | `@crystaldba/postgres-mcp` | Запросы/инспекция БД `bscout` | `--access-mode=restricted` (**read-only**); строка через `${BSCOUT_DB_URL:-...}` |
| `context7` | `@upstash/context7-mcp` | Актуальная докура библиотек | — |
| `playwright` | `@playwright/mcp` | Браузер / E2E фронтенда на :3000 | — |
| `security-scanner` | `agent-security-scanner-mcp` | Аудит зависимостей, git-diff, SBOM | — |

- Строку подключения к БД переопредели через env `BSCOUT_DB_URL` (см. `settings.local.json.example`). По умолчанию — dev-строка `postgresql://bscout:bscout@localhost:5434/bscout` (контейнер опубликован на host-порту **5434**: 5432/5433 были заняты другими локальными Postgres).
- Если `context7` / `security-scanner` требуют API-ключ — экспортируй его в shell; `.mcp.json` подхватит из окружения. **Секреты в репо не хранить.**
- Управление: `claude mcp list`, `claude mcp get <name>`.

## Правила (`.claude/rules/`)

Авто-подгружаются, когда открыт/редактируется файл под `paths:`.

- `frontend.md` → `frontend/**/*.{ts,tsx,css}` — FSD-слои, `models/<entity>`, состояние (React Query + Effector), Tailwind-only, `@/*`.
- `backend.md` → `backend/**/*.py` — модульный MVC, всё async, camelCase JSON, без комментариев, статус Alembic.

## Скилы (`.claude/skills/`)

| Скил | Триггер | Что делает |
|------|---------|------------|
| `/backend-module` | «новый модуль/эндпоинт бэкенда» | Скаффолд `modules/<name>/` (model/schema/service/controller) + регистрация роутера в `main.py` |
| `/frontend-entity` | «модель/хуки/запросы на фронте» | Скаффолд `models/<entity>/` (schema.ts, service.ts, hooks.ts, index.ts) |
| `/design-system` | любая UI/вёрстка/стили | Читает `skills/claude/` (TypeUI) перед написанием JSX |
| `/project-conventions` | «проверь по стандартам» | Чеклист-ревью diff на соответствие конвенциям |

## Хуки (`.claude/settings.json` → `.claude/hooks/`)

| Событие | Скрипт | Действие |
|---------|--------|----------|
| `PreToolUse` (Read/Edit/Write/Bash) | `protect-secrets.sh` | Блокирует доступ к реальным `.env` (разрешает `*.example`) |
| `PostToolUse` (Edit/Write) | `frontend-format.sh` | `prettier --write` + `eslint --fix` для изменённых `frontend/**/*.{ts,tsx}` |
| `PostToolUse` (Edit/Write) | `backend-format.sh` | `ruff format` + `ruff check --fix` для изменённых `backend/**/*.py` |
| `Stop` | `build-lint-reminder.sh` | Если `frontend/src`/`backend/src` изменены — напоминает про build+lint |

Все хуки самофильтруются по пути и тихо пропускаются, если инструмент не установлен, — они не ломают работу.

## Статус инструментов

Бэкенд запускается через **venv + pip на Python 3.11** (poetry не установлен; venv в `bsout-pricer/venv`). Установка: `cd backend && pip install -r requirements-dev.txt`.

1. **ruff** — ✅ в `pyproject.toml` + `requirements-dev.txt`. В системе ruff тоже есть, хук работает.
2. **frontend deps** (для `frontend-format`): `cd frontend && npm install`.
3. **Alembic** — ✅ инициализирован (async/asyncpg) и **первая миграция применена** (`alembic/versions/fb0762d20565_initial_schema.py`, 7 таблиц). Новые: `python -m alembic revision --autogenerate -m "..."` → `python -m alembic upgrade head`. Каждую новую модель регистрировать импортом в `alembic/env.py`.

Доустановленные/зафиксированные зависимости (были не указаны или ломали запуск): `email-validator`, `greenlet`, `sqlalchemy[asyncio]`, и **`bcrypt==4.0.1`** (passlib 1.7.4 несовместим с bcrypt 5.x). `poetry.lock` устарел (правился вручную, в pip-workflow не используется).

## Соседние системы (не Claude Code)
- `.opencode/` — конфиг OpenCode (агенты/команды BMAD). Не трогается этим слоем.
- `AGENTS.md` (root/frontend/backend) — формат OpenCode; частично устарел (см. `CLAUDE.md`).
- `_bmad/` — BMAD Method.
