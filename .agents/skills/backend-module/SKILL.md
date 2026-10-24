---
name: backend-module
description: Implement or extend a BScout FastAPI backend module using current repository patterns.
---

Before feature work, read `docs/technical-specification.md` and
`backend/AGENTS.md`. Inspect one nearby module and follow its current
`model/`, `schema/`, `service/`, and `controller/` patterns. Keep async database
work, Python and API fields in `snake_case`, and register routers/models where
the repository currently requires. For schema changes, generate and inspect an
Alembic migration with the existing Python 3.11 venv and pip workflow; do not
assume migrations are unavailable. Add focused regression coverage for fixes.
Never read real `.env` files.
