---
name: bscout-orchestrate
description: Choose a cost-aware workflow and optional subagents for BScout tasks; use for task routing, delegation, or model selection.
---

Prefer direct execution by the main Sol agent for small, clear changes. Do not
create a separate coder to repeat work the main agent can complete directly.

For substantial exploration, delegate a bounded read-only question to bscout_reader
(Luna / medium), then let the main agent implement from the findings. Return only
relevant paths, lines, conclusions and open questions; do not reread the whole
repository after receiving sufficient evidence. Verify critical claims as needed.
Prefer a fresh, narrow context over forking all history when context cost matters.

For large tasks, delegate only useful independent work with explicit file ownership.
Use bscout_coder (Sol 6.1 / low) for a separate implementation only when that split
adds value. The main agent owns integration and proportional verification.

Use bscout_prompt_master (Luna / medium) when explicitly requested or when a large,
ambiguous task needs a reusable brief or handoff to another chat. Give it existing
reader findings; do not run a reader solely to feed a clear prompt. Skip prompt
rewriting for an already actionable task. Do not make the full role chain mandatory.
Use bscout_reviewer only for meaningful risks or an explicit review request.

Load only task-relevant skills and individual reference rules. Avoid speculative
refactoring, repeated broad checks and duplicate investigations. If a low-effort
attempt fails, diagnose the cause before retrying; when deeper reasoning is needed,
explain why and propose an effort change rather than repeating the same approach.
Preserve configured model/effort and user choices; do not silently escalate cost.

Report requested model and runtime metadata when available. A self-reported model
name is not billing evidence. If the requested model is unavailable, explain and
ask the user before substituting. Skills do not switch the primary model or prove
host configuration activation. Do not use Astra or Terra in this workflow unless
the user changes the model policy.

For examples and configuration notes, read
[references/usage.md](references/usage.md).
