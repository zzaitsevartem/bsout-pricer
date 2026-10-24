---
name: frontend-entity
description: Add or change a BScout frontend data entity, API service, schema, or query hooks.
---

Read `frontend/AGENTS.md` and inspect nearby `frontend/src/models/` entities.
Keep the established four-file entity shape (`schema.ts`, `service.ts`,
`hooks.ts`, `index.ts`), use Zod-derived types, the shared API client, React
Query for server state, and `@/*` imports. Match backend JSON casing. Add or
update focused tests for behavioral fixes, then use the relevant frontend checks.
