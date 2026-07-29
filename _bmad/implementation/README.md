# Implementation Phase Artifacts

> **Вход:** Story Prep-артефакт (`_bmad/story-prep/{task-id}.md`)
> **Агент:** dev (или quick-flow-solo-dev для малых задач)
> **Следующая фаза:** QA

## Структура артефакта

Каждый артефакт сохраняется как `_bmad/implementation/{task-id}.md`.

Полный шаблон: `docs/agents/agent-output-contracts.md#implementation`

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
```
