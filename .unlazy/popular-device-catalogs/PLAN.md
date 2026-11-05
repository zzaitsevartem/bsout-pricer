# Plan: popular device catalogs
Scope: popular-device-catalogs
Depth: tree 2
Mode: orchestrated
Contract revision: 1

## Contract
Popular suggestions must open the matching /devices/model_key catalog from the screenshot, on click and keyboard, consistently at all shared entry points. Keep curated labels, width, dismissal and typed search behavior. Luna audits catalog availability for every device, distinguishes routes from populated data and photos/specs; reports measured current coverage, not historical assumptions. Terra owns tests and supplies results to Luna; Luna collects final report. Driver only controls Luna reports and runs independent gate verification; no app edits by driver. No commits, real env reads, unrelated dirty changes or unnecessary server restarts. Existing branch codex/search-card-source has dirty backend and card changes; preserve them.
Toolchain: Node/npm, Python3.11 existing backend/venv, repo cwd and /bin/sh. Native sequential waves, max 3 active agents. Read required skills/rules before implementation. Amend exact ownership before new files.

## Current contract inventory
| ID | Required outcome or constraint | Owner | Observing gate | Disposition | Revision |
|---|---|---|---|---|---|
| C1 | Popular iPhone15–11 opens matching device catalog by click/keyboard | 1.1,1.2 | GATES:G1 | ACTIVE | 1 |
| C2 | Shared entry points, width and existing search/device selection preserved | 1.1,1.2 | GATES:G1 | ACTIVE | 1 |
| C3 | Current catalog availability checked for all devices, data/photo/spec coverage distinguished | 1.1 | leaf-1.1:G1 | ACTIVE | 1 |
| C4 | Luna gathers research and Terra test evidence; driver controls reports | 1.3 | leaf-1.3:G1 | ACTIVE | 1 |

## Tree
- 1 Popular catalogs integration — GATES.md
  - 1.1 Luna catalog audit and routing — gates/leaf-1.1.md
  - 1.2 Terra tests — gates/leaf-1.2.md
  - 1.3 Luna combined report — gates/leaf-1.3.md

## Leaf dispatch table
| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1 | frontend/src/widgets/ProductSearch/ui/ProductSearchField.tsx, frontend/src/widgets/Header/ui/HeaderSearch.tsx, frontend/src/widgets/authorizedHome/ui/AuthorizedHero.tsx, frontend/src/app/search/_components/SearchInput.tsx, .unlazy/popular-device-catalogs/research.md | - | judgment | 1 | VERIFIED |
| 1.2 | frontend/src/widgets/ProductSearch/ui/ProductSearchField.test.tsx, frontend/src/widgets/ProductSearch/ui/DeviceSearch.test.tsx, frontend/src/app/search/_components/SearchInput.test.tsx, backend/tests/integration/test_device_pages.py | 1.1 | judgment | 2 | VERIFIED |
| 1.3 | .unlazy/popular-device-catalogs/report.md, gptaudits/61.md, docs/plan/MASTERPLAN.md | 1.2 | judgment | 3 | VERIFIED |
