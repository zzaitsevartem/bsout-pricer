# AGENTS.md — BScout Pricer

> Инструкции для AI-агентов, работающих с проектом BScout Pricer.
> Проект использует **BMAD** (Business → Model → Architecture → Development) — методологию
> поэтапной разработки через специализированных агентов.

---

## 1. Быстрый старт

```bash
# === Frontend (Next.js 14 + Tailwind + shadcn/ui) ===
cd frontend && npm run dev        # Dev-сервер на :3000
cd frontend && npm run build      # Production-сборка
cd frontend && npm run lint       # ESLint + TypeScript проверка

# === Backend (FastAPI + SQLAlchemy + Alembic) ===
cd backend && uvicorn src.main:app --reload   # Dev-сервер на :8000

# === Docker (PostgreSQL 16 + Redis 7) ===
docker compose -f docker/docker-compose.yml up -d
```

---

## 2. Структура проекта

```
bscout-pricer/
├── frontend/          # Next.js 14 + Tailwind + shadcn/ui + FSD
├── backend/           # FastAPI + SQLAlchemy + Alembic + Redis
├── docker/            # docker-compose.yml (PostgreSQL 16 + Redis 7)
├── docs/              # ТЗ, бизнес-план, дизайн, контракты агентов
│   └── agents/        # Контракты выходных артефактов BMAD
├── _bmad/             # BMAD-модули: агенты, воркфлоу, артефакты фаз
│   ├── _config/       # Манифесты и глобальная конфигурация
│   ├── core/          # Ядро BMAD (master-агент, базовые задачи/воркфлоу)
│   ├── bmm/           # Business Model Maturity (9 агентов полного цикла)
│   ├── bmb/           # Module Builder (создание/поддержка BMAD-модулей)
│   ├── cis/           # Creative Innovation & Strategy (креативные методики)
│   ├── tea/           # Testing & Education Automation
│   ├── discovery/     # Артефакты discovery-фазы
│   ├── product/       # Артефакты product/UX-фазы
│   ├── architecture/  # Артефакты архитектурной фазы
│   ├── story-prep/    # Артефакты фазы подготовки задач
│   ├── implementation/ # Артефакты фазы реализации
│   ├── qa/            # Артефакты фазы тестирования
│   └── handoff/       # Артефакты фазы сдачи
├── .opencode/         # Регистрация агентов и команд для opencode
│   ├── agent/         # 20 файлов-прокси к агентам в _bmad/
│   └── command/       # 56 файлов-прокси к воркфлоу в _bmad/
├── opencode.jsonc     # Конфигурация opencode (регистрирует agent/ и command/)
└── AGENTS.md          # Этот файл
```

---

## 3. BMAD-цикл разработки

```
Пользователь → Discovery → Product/UX → Architecture → Story Prep → Implementation → QA → Handoff
```

Каждая фаза:
1. Получает входной артефакт от предыдущей фазы
2. Выполняет свою работу через специализированного агента
3. Создаёт выходной артефакт в `_bmad/{phase}/{task-id}.md`
4. Передаёт результат следующей фазе

**Контракты всех фаз:** `docs/agents/agent-output-contracts.md`

---

## 4. Агенты BMAD

### 4.1 Core — ядро системы

| Агент | Файл | Назначение |
|-------|------|------------|
| **bmad-master** | `_bmad/core/agents/bmad-master.md` | Оркестратор цикла: `/status`, `/phase`, `/agents`, `/help` |

### 4.2 BMM — полный цикл (9 агентов)

| Агент | Файл | Фаза | Назначение |
|-------|------|------|------------|
| **analyst** | `_bmad/bmm/agents/analyst.md` | Discovery → Product | Сбор и структурирование требований |
| **ux-designer** | `_bmad/bmm/agents/ux-designer.md` | Product/UX | Исследование юзеров, прототипы, CJM |
| **architect** | `_bmad/bmm/agents/architect.md` | Architecture | Проектирование тех. архитектуры, ADR |
| **pm** | `_bmad/bmm/agents/pm.md` | все фазы | Планирование, трекинг, риски |
| **sm** | `_bmad/bmm/agents/sm.md` | все фазы | Agile-коучинг, фасилитация, метрики |
| **dev** | `_bmad/bmm/agents/dev.md` | Implementation | Написание кода, тестов, документации |
| **qa** | `_bmad/bmm/agents/qa.md` | QA | Верификация AC, тестирование, отчёт |
| **tech-writer** | `_bmad/bmm/agents/tech-writer/tech-writer.md` | все фазы | Документирование API, архитектуры, мануалов |
| **quick-flow-solo-dev** | `_bmad/bmm/agents/quick-flow-solo-dev.md` | Quick Flow | Быстрые изолированные задачи (баги, мелкие фичи) |

### 4.3 BMB — строительство BMAD (3 агента)

| Агент | Файл | Назначение |
|-------|------|------------|
| **agent-builder** | `_bmad/bmb/agents/agent-builder.md` | Создание и поддержка BMAD-агентов |
| **module-builder** | `_bmad/bmb/agents/module-builder.md` | Создание и поддержка BMAD-модулей |
| **workflow-builder** | `_bmad/bmb/agents/workflow-builder.md` | Создание и поддержка BMAD-воркфлоу |

### 4.4 CIS — креатив и стратегия (6 агентов)

| Агент | Файл | Назначение |
|-------|------|------------|
| **brainstorming-coach** | `_bmad/cis/agents/brainstorming-coach.md` | Фасилитация мозговых штурмов |
| **creative-problem-solver** | `_bmad/cis/agents/creative-problem-solver.md` | Решение сложных проблем |
| **design-thinking-coach** | `_bmad/cis/agents/design-thinking-coach.md` | Дизайн-мышление |
| **innovation-strategist** | `_bmad/cis/agents/innovation-strategist.md` | Инновационные стратегии |
| **presentation-master** | `_bmad/cis/agents/presentation-master.md` | Создание презентаций |
| **storyteller** | `_bmad/cis/agents/storyteller.md` | Сторителлинг |

### 4.5 TEA — тестирование и обучение (1 агент)

| Агент | Файл | Назначение |
|-------|------|------------|
| **tea** | `_bmad/tea/agents/tea.md` | ATDD, автотесты, CI, NFR, traceability |

---

## 5. Как выбрать агента

| Ситуация | Какой агент |
|----------|-------------|
| «Нужно реализовать фичу» | **dev** (или **quick-flow-solo-dev** для мелочи) |
| «Собери требования» | **analyst** → **ux-designer** |
| «Спроектируй архитектуру» | **architect** |
| «Нужен план/статус проекта» | **pm** |
| «Проведи ретро/стендап» | **sm** |
| «Проверь качество» | **qa** |
| «Напиши документацию» | **tech-writer** |
| «Придумай идеи / решение» | **brainstorming-coach** / **creative-problem-solver** |
| «Создай нового агента» | **agent-builder** |
| «Создай новый модуль» | **module-builder** |
| «Создай новый воркфлоу» | **workflow-builder** |

---

## 6. Команды (Workflows)

Проект содержит **56 предустановленных команд-воркфлоу** в `.opencode/command/`.
Основные группы:

| Группа | Примеры | Назначение |
|--------|---------|------------|
| **Core** | `help`, `party-mode`, `review-*` | Базовые утилиты |
| **BMM — Analysis** | `domain-research`, `market-research`, `create-product-brief` | Исследования |
| **BMM — Planning** | `sprint-planning`, `sprint-status`, `retrospective` | Планирование |
| **BMM — Architecture** | `create-architecture`, `create-prd`, `validate-prd` | Архитектура |
| **BMM — Implementation** | `dev-story`, `code-review`, `correct-course` | Реализация |
| **BMM — QA** | `qa-generate-e2e-tests` | Тестирование |
| **BMB** | `create-agent`, `create-module`, `validate-workflow` | Сборка BMAD |
| **CIS** | `brainstorming`, `problem-solving`, `storytelling` | Креатив |
| **TEA** | `testarch-atdd`, `testarch-automate`, `teach-me-testing` | Тест-архитектура |

Полный список команд: `ls .opencode/command/`

---

## 7. Соглашения (Conventions)

### Общие
- Все новые файлы создавать только по запросу пользователя
- Не запускать `git commit` без явной просьбы
- Не создавать README/doc-файлы без явной просьбы

### Дизайн и фронтенд
- ALWAYS читать `DESIGN.md` перед началом работы над дизайном/фронтендом
- После изменений запускать `npm run build && npm run lint`
- Следовать FSD (Feature-Sliced Design) архитектуре фронтенда

### Архитектура и фичи
- ALWAYS читать `docs/technical-specification.md` перед реализацией новой фичи
- ALWAYS читать `docs/agents/agent-output-contracts.md` перед созданием артефакта фазы
- Следовать BMAD-циклу: каждая задача проходит фазы Discovery → ... → Handoff
- Артефакты сохранять в `_bmad/{phase}/{task-id}.md` по контракту фазы

### Код
- Писать код без комментариев (если не запрошены явно)
- Без `any` и `@ts-ignore`
- Без хардкода (ключи, URL, env-специфичные значения)
- Unit + integration тесты обязательны для новой логики
- ESLint и TypeScript check должны проходить

---

## 8. Файловая система _bmad/

```
_bmad/
├── _config/
│   └── agent-manifest.csv         # Манифест 7 агентов BMAD-цикла
├── core/
│   ├── agents/bmad-master.md      # Мастер-оркестратор
│   ├── tasks/                     # help, editorial-review, index-docs, shard-doc
│   └── workflows/                 # party-mode, brainstorming
├── bmm/
│   ├── agents/                    # 9 агентов полного цикла
│   └── workflows/                 # 23 воркфлоу по фазам
├── bmb/
│   ├── agents/                    # 3 агента-строителя BMAD
│   └── workflows/                 # 12 воркфлоу создания/валидации
├── cis/
│   ├── agents/                    # 6 креативных агентов
│   └── workflows/                 # 5 воркфлоу
├── tea/
│   ├── agents/tea.md             # Агент тест-архитектуры
│   └── workflows/                 # 10 воркфлоу
├── discovery/         → артефакты фазы исследования
├── product/           → артефакты фазы продукта
├── architecture/      → артефакты фазы архитектуры
├── story-prep/        → артефакты фазы подготовки задач
├── implementation/    → артефакты фазы реализации
├── qa/                → артефакты фазы тестирования
└── handoff/           → артефакты фазы сдачи
```
