---
name: bscout-design-system
description: Build or change BScout UI and styling using the current project design system.
---

Before UI work, read `DESIGN.md`, `frontend/AGENTS.md`, and inspect the current
implementation in `frontend/tailwind.config.ts`, `frontend/src/app/globals.css`,
and nearby components. Those files define the active tokens and patterns; older
design libraries or prose do not override them. Use existing Tailwind tokens,
components, and button classes instead of introducing hardcoded colors,
typography, shadows, or parallel styling systems. Preserve responsive behavior,
semantic HTML, keyboard access, focus states, and light/dark themes.
