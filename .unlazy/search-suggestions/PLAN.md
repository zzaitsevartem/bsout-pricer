# Plan: Search suggestions
Scope: search-suggestions
Depth: tree 2
Mode: orchestrated
Contract revision: 1

## Contract
Shared ProductSearchField; public props and backend response preserved. Driver owns implementation and integration. Luna reads, Terra owns tests, Luna collects final evidence. Sequential native subagent waves; max one child running. Node/npm, repository cwd, /bin/sh. No real env reads, server restarts or commits. Reuse design tokens and keyboard behavior.

## Current contract inventory
| ID | Required outcome or constraint | Owner | Observing gate or manual review | Disposition | Revision |
|---|---|---|---|---|---|
| C1 | Empty focused input shows Часто ищут with iPhone 15, 14, 13, 12 etc | root | GATES:G2 | ACTIVE | 1 |
| C2 | Panel stays within search width on desktop/mobile | root | GATES:G3 | ACTIVE | 1 |
| C3 | Suggestions show model before part for every structured device/part | root | GATES:G2 | ACTIVE | 1 |
| C4 | Selection/navigation/history and keyboard remain working | root | GATES:G2 | ACTIVE | 1 |
| C5 | Luna reads, Terra writes tests, Luna reports, driver verifies/reassigns gaps | leaf-1.1, leaf-1.2, leaf-1.3 | GATES:G1 | ACTIVE | 1 |

## Tree
- 1 Search changes — GATES.md
  - 1.1 Luna source research — gates/leaf-1.1.md
  - 1.2 Terra regression tests — gates/leaf-1.2.md
  - 1.3 Luna final evidence report — gates/leaf-1.3.md

## Leaf dispatch table
| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1 | .unlazy/search-suggestions/research.md | - | judgment | 1 | VERIFIED |
| 1.2 | frontend/src/widgets/ProductSearch/ui/ProductSearchField.test.tsx, backend/tests/unit/test_suggestion_display.py, backend/tests/integration/test_comparison_api.py | 1.1 | judgment | 2 | VERIFIED |
| 1.3 | .unlazy/search-suggestions/report.md | 1.2 | judgment | 3 | VERIFIED |
