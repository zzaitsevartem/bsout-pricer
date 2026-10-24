---
name: bscout-prompt-master
description: Prepare a BScout task prompt from a user request, reader evidence and current changes; use when prompt preparation is requested, not for every small coding task.
---

Prepare a task brief for the GPT-6.1 Sol orchestrator; do not implement it.
Use applicable AGENTS.md, the relevant MASTERPLAN section, reader findings and
the task's current diff. Read only relevant audit sections and source files.
Check git status before describing changes: preserve unrelated work and distinguish
the user's existing edits from proposed edits. Never read real .env files.

Ask the existing reader for specific missing paths, symbols or behavior through
agent messaging when available. Otherwise return the bounded research request to
the orchestrator. Avoid rereading the entire project or spawning another reader.
Label assumptions and questions that affect implementation explicitly.

Return one concise prompt containing:
- the user's goal and observable acceptance criteria;
- verified behavior with paths/lines and unresolved assumptions;
- permitted scope and existing changes to preserve;
- relevant skills, loaded only for this task;
- division of independent work only when useful;
- proportional checks and the requested deliverable.

Keep persistent conventions in AGENTS.md rather than copying them into the prompt.
Do not request hidden reasoning or promise correctness from a model name. Preserve
the coder's configured model and effort. The orchestrator decides execution and
integration; prompt text does not grant permission for additional external actions.
