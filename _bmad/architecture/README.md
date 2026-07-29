# Architecture Phase Artifacts

> **Вход:** Product-артефакт (`_bmad/product/{task-id}.md`)
> **Агент:** architect
> **Следующая фаза:** Story Prep

## Структура артефакта

Каждый артефакт сохраняется как `_bmad/architecture/{task-id}.md`.

Полный шаблон: `docs/agents/agent-output-contracts.md#architecture`

```markdown
# Architecture: {Название}

## Architectural Style
{монолит / микросервисы / event-driven}

## Technology Stack
- Frontend: {...}
- Backend: {...}
- Database: {...}

## Module Decomposition
- {module}: {responsibility}

## API Contracts
- {endpoint}: {method, request, response}

## NFR Decisions
- Performance: {решение}
- Security: {решение}

## ADR
- {ADR-1}: {решение, последствия}
```
