# Agent Output Contracts

> Единый реестр контрактов выходных артефактов для каждой фазы BMAD-цикла.
> Каждая фаза принимает вход от предыдущей и produces строго определённый набор артефактов.

---

## Discovery

**ID:** `DIS-01`
**Вход:** бизнес-гипотеза / задача / проблемное описание от пользователя
**Выход:** `_bmad/discovery/{task-id}.md`

### Структура артефакта

```markdown
# Discovery: {Название задачи}

## Problem Statement
{core problem statement}

## Context
{контекст, предпосылки, триггер}

## Stakeholders
- {имя / роль}: {интересы, ожидания}

## Boundaries
- **Входит:** {что в scope}
- **Не входит:** {что out-of-scope}

## Success Criteria
- [ ] {критерий приёмки задачи}
- [ ] {критерий приёмки задачи}

## Constraints
- {технические/бизнесовые ограничения}

## Open Questions
- {вопрос}
```

---

## Product / UX

**ID:** `PRO-01`
**Вход:** Discovery-артефакт (`_bmad/discovery/{task-id}.md`)
**Выход:** `_bmad/product/{task-id}.md`

### Структура артефакта

```markdown
# Product: {Название продукта/фичи}

## Target Audience
- {сегмент}: {роль, цели, боли}

## Value Proposition
{уникальное ценностное предложение}

## User Stories
- {FR-1}: {описание}
- {FR-2}: {описание}

## Non-Functional Requirements
- {NFR-1}: {описание}

## UX Decisions
- {решение}: {обоснование}

## Success Metrics
- North Star: {метрика}
- Leading: {метрики}
- Lagging: {метрики}

## Out of Scope
- {что не делаем сейчас}
```

---

## Architecture

**ID:** `ARC-01`
**Вход:** Product-артефакт (`_bmad/product/{task-id}.md`)
**Выход:** `_bmad/architecture/{task-id}.md`

### Структура артефакта

```markdown
# Architecture: {Название}

## Architectural Style
{монолит / микросервисы / event-driven / иное}

## Technology Stack
- Frontend: {React / Next.js / ...}
- Backend: {NestJS / FastAPI / ...}
- Database: {PostgreSQL / ...}
- Infrastructure: {Docker / ...}

## Module / Service Decomposition
- {module-1}: {responsibility}
- {module-2}: {responsibility}

## API Contracts
- {endpoint}: {method, request, response}

## Data Model (ERD)
{описание ключевых сущностей}

## NFR Decisions
- Performance: {решение}
- Security: {решение}
- Availability: {решение}

## Risks & Mitigations
- {риск}: {митигация}

## ADR (Architecture Decision Records)
- {ADR-1}: {решение, контекст, последствия}
```

---

## Story Prep

**ID:** `STO-01`
**Вход:** Architecture-артефакт (`_bmad/architecture/{task-id}.md`)
**Выход:** `_bmad/story-prep/{task-id}/` (директория с историями)

### Структура артефакта (одна story)

```markdown
# Story: {BSOUT-NNN} — {Краткое название}

## Description
{описание задачи}

## Acceptance Criteria
- [ ] AC-1: {критерий}
- [ ] AC-2: {критерий}

## Technical Context
{ссылки на архитектуру, ADR, контракты}

## Files to Change
- {путь}: {что меняется}

## Estimation
{XS / S / M / L / XL}

## Dependencies
- {story-id}: {тип зависимости}
```

---

## Implementation

**ID:** `IMP-01`
**Вход:** Story Prep-артефакт (`_bmad/story-prep/{task-id}/`)
**Выход:** `_bmad/implementation/{task-id}.md`

### Структура артефакта

```markdown
# Implementation: {BSOUT-NNN}

## Changes Made
- {file}: {что сделано}

## Test Coverage
- Unit: {кол-во тестов, покрытие}
- Integration: {кол-во тестов}

## Verification
- [ ] Линтер пройден
- [ ] Typecheck пройден
- [ ] Тесты проходят
- [ ] MR открыт

## Notes
{особенности реализации, open questions}
```

---

## QA

**ID:** `QA-01`
**Вход:** Implementation-артефакт (`_bmad/implementation/{task-id}.md`)
**Выход:** `_bmad/qa/{task-id}.md`

### Структура артефакта

```markdown
# QA Report: {BSOUT-NNN}

## Test Results
- Smoke: {PASS / FAIL}
- Functional: {PASS / FAIL}
- Regression: {PASS / FAIL}

## AC Verification
- [ ] AC-1: {PASS / FAIL}
- [ ] AC-2: {PASS / FAIL}

## Bugs Found
- {BUG-1}: {severity, steps, expected/actual}

## Verdict
{PASS / Conditional Pass / FAIL}
```

---

## Handoff

**ID:** `HAN-01`
**Вход:** QA-отчёт (`_bmad/qa/{task-id}.md`)
**Выход:** `_bmad/handoff/{task-id}.md`

### Структура артефакта

```markdown
# Handoff: {BSOUT-NNN / Спринт / Этап}

## Done
- {что сделано}

## Not Done
- {что не сделано и почему}

## Risks
- {открытые риски}

## Next Steps
- {рекомендации}

## Artifacts
- {ссылки на артефакты фаз}
```
