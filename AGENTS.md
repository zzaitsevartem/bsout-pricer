# AGENTS.md — BScout (root)

Инструкции для AI-агентов, работающих с проектом BScout.

## Команды

```bash
# Frontend
cd frontend && npm run dev      # Dev server на :3000
cd frontend && npm run build    # Production сборка
cd frontend && npm run lint     # ESLint

# Backend
cd backend && uvicorn src.main:app --reload  # Dev server на :8000

# Docker
docker compose -f docker/docker-compose.yml up -d  # PostgreSQL + Redis
```

## Структура

```
bscout/
├── frontend/    # Next.js 14 + Tailwind + shadcn/ui + FSD
├── backend/     # FastAPI + SQLAlchemy + Alembic
├── docker/      # docker-compose.yml (PostgreSQL 16 + Redis 7)
└── docs/        # ТЗ и бизнес-план
```

## Ключевые файлы

- **DESIGN.md** — полное описание дизайна, цветов, шрифтов, анимаций, FSD-структуры
- `docs/technical-specification.md` — ТЗ на 7 этапов
- `docs/bussines-plan.md` — бизнес-план

## Соглашения

- Все новые файлы создавать только по запросу пользователя
- ALWAYS читать DESIGN.md перед началом работы над дизайном/фронтендом
- ALWAYS читать technical-specification.md перед реализацией новой фичи
- После изменений запускать `npm run build` и `npm run lint` для фронтенда
- Не запускать `git commit` без явной просьбы пользователя
- Не создавать README/doc-файлы без явной просьбы
