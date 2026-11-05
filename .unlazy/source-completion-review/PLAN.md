# Plan: источник на реальных поисковых карточках

Scope: source-completion-review
Depth: tree 2, two branches
Mode: orchestrated

## Contract

Revision 3: user reports every live card displays unavailable source. Diagnose and correct the actual runtime/data path; a fallback is not acceptance. Luna owns source reading, diagnosis and report; Terra owns corrective implementation/runtime updates, tests and live probes; main owns coordination and report review only and does not edit production code, operate services or run tests. No commits, real .env reads, user browser takeover or unrelated changes.
Interfaces: source binds the displayed minimum retail price to the exact filtered offer/store/URL; missing data must not mask a stale runtime.
Toolchain: repository cwd, existing Python venv and frontend dependencies, native Codex agents. Sequential check execution. No inherited CHECK execution without inspection.
Host launch mode: native agents, two concurrent leaves in wave 1. Agent model routing preserved: Luna reader, Terra tests.

## Current contract inventory

| ID | Required outcome or constraint | Owner | Observing gate or manual review | Disposition | Revision |
|---|---|---|---|---|---|
| C1 | Explain actual changes and distinguish authors | leaf-1.1.1 | leaf-1.1.1:G1 | MET | 3 |
| C2 | Diagnose stale runtime and provide corrective action | leaf-1.1.1 | leaf-1.1.1:G2 | MET | 3 |
| C3 | Deploy source schema and prove real API source; distinguish rendered UI proof | leaf-1.2.1 and root | leaf-1.2.1:G1-G3 | ACTIVE | 3 |
| C4 | Preserve filtered selection, ties, detail and no-offer behavior | leaf-1.2.1 | Terra regression evidence in report (pre-rebuild, unchanged source) | MET | 3 |
| C5 | Luna reads all results and main judges completeness | root | GATES:G1 | ACTIVE | 3 |
| C6 | No unrelated data/process/session damage, no commits | root | GATES:G2 | ACTIVE | 3 |

## Tree

- 1 Source completion review and fix ... GATES.md
  - 1.1 Evidence and diagnosis ... gates/node-1.1.md
    - 1.1.1 Luna report ... gates/leaf-1.1.1.md
  - 1.2 Actual behavior ... gates/node-1.2.md
    - 1.2.1 Terra checks ... gates/leaf-1.2.1.md

## Leaf dispatch table

| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1.1 | .unlazy/source-completion-review/report.md, .unlazy/source-completion-review/PLAN.md, .unlazy/source-completion-review/gates/leaf-1.1.1.md, .unlazy/source-completion-review/status.log, gptaudits/60.md | - | judgment | 1 | VERIFIED |
| 1.2.1 | .unlazy/source-completion-review/results/** | - | judgment | 1 | ABANDONED |
