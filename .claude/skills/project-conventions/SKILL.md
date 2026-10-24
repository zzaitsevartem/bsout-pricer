---
name: project-conventions
description: >
  BScout code review entrypoint; follow .agents/skills/project-conventions/SKILL.md
  and the applicable AGENTS.md files.
argument-hint: "[path-or-empty]"
allowed-tools: Read, Grep, Glob, Bash(git diff *), Bash(git status)
---

Review the requested paths or current diff using
`.agents/skills/project-conventions/SKILL.md` and applicable `AGENTS.md`
files. Report concrete findings with file and line. Do not change code unless
the user requested implementation.
