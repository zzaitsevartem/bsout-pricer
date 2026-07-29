# QA Phase Artifacts

> **Вход:** Implementation-артефакт (`_bmad/implementation/{task-id}.md`)
> **Агент:** qa
> **Следующая фаза:** Handoff

## Структура артефакта

Каждый артефакт сохраняется как `_bmad/qa/{task-id}.md`.

Полный шаблон: `docs/agents/agent-output-contracts.md#qa`

```markdown
# QA Report: {BSOUT-NNN}

## Test Results
- Smoke: {PASS / FAIL}
- Functional: {PASS / FAIL}
- Regression: {PASS / FAIL}

## AC Verification
- [ ] AC-1: {PASS / FAIL}

## Bugs Found
- {BUG-1}: {severity, steps}

## Verdict
{PASS / Conditional Pass / FAIL}
```
