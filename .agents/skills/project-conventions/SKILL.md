---
name: project-conventions
description: Review BScout changes for repository conventions and scoped verification.
---

Review the requested paths or current diff against `AGENTS.md` and the relevant
nested rules. Check only applicable conventions, cite findings with file and
line, and distinguish verified behavior from assumptions. For Python use the
repository's Python 3.11 venv and pip workflow; for schema changes inspect
Alembic migrations. Do not read real `.env` files. Recommend checks that match
the risk and changed area; avoid unrelated full-suite runs.
