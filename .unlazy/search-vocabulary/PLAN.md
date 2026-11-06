# Plan: search vocabulary

Scope: search-vocabulary
Depth: tree 2
Mode: orchestrated

## Contract

Revision 2. The accepted specification is vocabulary-audit.md. Main coordinates and reviews evidence only; Sol low owns production; Terra owns tests/runtime; Luna reads and reviews. No new dependencies, persisted normalization, migrations, UI edits, real .env reads, production DB writes, or unrelated service changes. Query spelling remains visible unchanged. Decisions about EXPLAIN, budget and fuzzy ordering precede the patch. Explicit model negatives take precedence over legacy short-token substring false positives: recognized SE/XR/GT/Pro and SKU pieces may receive boundaries; ordinary words retain literal behavior. Baseline removals must be documented and tested.

Host: native Codex agents, maximum two children. Wave 1 launches coder and Terra together for design/preflight. Terra sends EXPLAIN evidence before coder patches; final tests await coder. Wave 2 launches Luna for independent reading after coder returns; final review waits for Terra evidence. This staged review has no dispatch dependency, but cannot finish without final test/runtime results. Sequential gate checks; Python 3.11 existing venv preferred (absent here; Terra must document isolated Python 3.11 fallback); repository CWD and /bin/sh. Main may run orchestration checks but application checks are executed by Terra, including independent re-verification.

## Current contract inventory

| ID | Required outcome or constraint | Owner | Observing gate or manual review | Disposition | Revision |
|---|---|---|---|---|---|
| C1 | All-plan layout, bidirectional е/ё, bounded confirmed translit, original candidate first | leaf-1.1 | G1, G2 and Luna | ACTIVE | 1 |
| C2 | AND words, safe regex/model/SKU boundaries (narrow legacy false-positive correction), finite expansion budget | leaf-1.1 | G1, leaf-1.2:G1 and Luna | ACTIVE | 2 |
| C3 | Preserve aliases, Advanced typo flag, raw-query fuzzy ordering, price order and pagination | leaf-1.1 | G2, leaf-1.2:G1 and Luna | ACTIVE | 1 |
| C4 | All relevant endpoints retain store/price/stock/device/part/quality/category filters | leaf-1.2 | G1 and Luna | ACTIVE | 1 |
| C5 | Positive and competing negative matrix, baseline comparison, separate unit/integration and Ruff | leaf-1.2 | G1 | ACTIVE | 1 |
| C6 | Prepatch representative EXPLAIN, no unmeasured column functions or migration | leaf-1.2 | G2 | ACTIVE | 1 |
| C7 | Backend-only rebuilt runtime, health/OpenAPI/authenticated real-data read-only API | leaf-1.2 | G3 | ACTIVE | 1 |
| C8 | Isolated browser original query and suggestions; explicit handoff if unavailable | leaf-1.2 | G4 | ABANDONED | 1 |
| C9 | Source-grounded independent review and specification clarification | leaf-1.3 | G1 | ACTIVE | 1 |
| C10 | Preserve unrelated work and environments, no commit, audit and live plan | root | N2 | ACTIVE | 1 |

## Tree

- 1 Search vocabulary integration: GATES.md
  - 1.1 Query expansion: gates/leaf-1.1.md
  - 1.2 Tests and runtime: gates/leaf-1.2.md
  - 1.3 Independent source review: gates/leaf-1.3.md

## Leaf dispatch table

| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1 | backend/src/modules/products/service/search_predicate.py, backend/src/modules/catalog/service/normalizer.py | - | judgment | 1 | VERIFIED |
| 1.2 | backend/tests/unit/test_search_predicate.py, backend/tests/unit/test_normalizer.py, backend/tests/integration/test_search_vocabulary.py, .unlazy/search-vocabulary/test-evidence.md, .unlazy/search-vocabulary/checks/** | - | judgment | 1 | ABANDONED |
| 1.3 | .unlazy/search-vocabulary/review.md, docs/technical-specification.md | - | judgment | 2 | VERIFIED |

Terra preflight/test design is independent; final integration/runtime needs coder's completed patch. Record that barrier in evidence, do not infer success from dispatch completion.
