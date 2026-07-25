---
name: project-conventions
description: >
  Чеклист-ревью изменений на соответствие конвенциям BScout (backend FastAPI +
  frontend Next.js/FSD). Используй, когда просят проверить/поревьюить код на
  соответствие стандартам проекта, или перед завершением задачи как самопроверку.
argument-hint: "[path-or-empty]"
allowed-tools: Read, Grep, Glob, Bash(git diff *), Bash(git status)
---

# Ревью по конвенциям BScout

Проверь изменения (по умолчанию — рабочий diff; если задан `$1` — этот путь).

Текущий diff для контекста:
!`git status --porcelain && echo '---' && git diff --stat`

## Backend-чеклист (`backend/**/*.py`)
- [ ] Все эндпоинты и обращения к БД — `async`.
- [ ] Структура модуля: `model/ schema/ service/ controller/`; `controller/__init__.py` экспортирует `<name>_router`.
- [ ] Роутер зарегистрирован в `src/main.py`.
- [ ] snake_case в Python, camelCase в JSON (`model_config`).
- [ ] **Нет docstring и комментариев** в коде.
- [ ] Авторизация через `Depends(get_current_user)` / `get_current_admin`.
- [ ] Схемы — Pydantic v2; модели наследуют `Base`.
- [ ] Новые таблицы не полагаются на несуществующий Alembic.

## Frontend-чеклист (`frontend/**/*.{ts,tsx}`)
- [ ] Слой данных — `models/<entity>/` из 4 файлов (schema/service/hooks/index).
- [ ] Серверное состояние — React Query; клиентская авторизация — Effector (`shared/config/store.ts`).
- [ ] `"use client"` только при наличии React-хуков.
- [ ] Импорты через `@/*`, не относительные.
- [ ] Только Tailwind-утилиты; цвета/шрифты/анимации — из `tailwind.config.ts`.
- [ ] Условные классы через `cn()`.
- [ ] Токены не хардкодятся; дизайн сверен с `skills/claude/` (см. `/design-system`).

## Общее
- [ ] `.env` не читается и не коммитится (только `.env.example`).
- [ ] Нет лишних doc/README-файлов без запроса.
- [ ] Прогнаны `npm run build && npm run lint` (frontend) / проверен импорт `src.main` (backend).

Выдай результат списком: что нарушает конвенции (файл:строка) и как исправить. Не меняй код без явного запроса.
