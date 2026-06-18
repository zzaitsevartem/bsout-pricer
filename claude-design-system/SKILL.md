---
name: "claude-design-system"
description: "Claude Design System design system for AI coding agents."
metadata:
  author: typeui.sh
  source: workspace-importer
  projectName: "Claude"
  projectLogoUrl: ""
  importSource: "Manual TypeUI setup"
  primaryColorReference: "#18181b"
  surfaceColorReference: "#ffffff"
  textColorReference: "#09090b"
  typographyScale: "Inter-style sans serif, 12/14/16/20/24/32 scale, medium labels, semibold headings."
  spacingScale: "4px base grid with 8px, 12px, 16px, 24px, and 32px layout steps."
  radiusScale: "6px controls, 8px cards, 12px overlays, nested radii reduced by inner padding."
---

# Design System — Agent Instructions

This skill describes the visual design language for all UI output. Every component, layout, and page should follow the design specs in the module files below. These describe *what the design looks like* — you choose how to implement the styles.

## Style
A research-journal aesthetic printed on warm stone — authoritative, editorial, almost achromatic. Pages live on warm ivory parchment (never pure white), with near-black slate as the dominant ink. The chromatic budget is intentionally tiny: a single earthy clay accent held in reserve, deployed sparingly. Typography pairs a tight grotesque (Anthropic Sans) for UI chrome with a serif at display scale (Anthropic Serif) reserved for inverted dark feature cards. Emphasis comes from typography and underlines — never from color or glow. Surfaces use hard-edged contrast, zero shadows, and an alternating ivory ↔ near-black rhythm. Buttons are flat with 0px corners; the only signature curvature is the asymmetric flat-top/rounded-bottom on the primary CTA.

## Before Writing Any Code

1. **Read every module that applies.** For a landing page, read at minimum: `layout.md`, `typography.md`, `colors.md`, `buttons.md`, `cards.md`, `shadows.md`, `radius.md`, `borders.md`. Do NOT write JSX until you have loaded all relevant modules.

## Critical Rules

- **Tokens are AGNOSTIC, framework-independent names:** The tokens defined in the `.md` files (like `neutral-primary-soft`, `heading`, `border-default`) are agnostic design system tokens, NOT literal class names from any CSS framework. Do not blindly use them as utility classes — you must explicitly map them in your styling layer (CSS variables, theme config, design tokens, etc.) before referencing them. You must implement the mapping yourself.

- **Cross-reference modules.** A card containing buttons must satisfy both `cards.md` AND `buttons.md`.
- **Dark mode is automatic.** The CSS custom properties resolve differently in light/dark via `@media (prefers-color-scheme: dark)`. Never manually swap colors.
- **Every interactive element needs hover, focus, and disabled states** — defined in the relevant module.
- **Use semantic HTML:** proper heading hierarchy (`h1`→`h6`), `<button>` for actions, `<a>` for navigation, ARIA attributes where needed.
- **Never use pure white (#FFFFFF) or pure black (#000000)** for any surface. Page bases use warm ivory; the darkest surface is slate-dark (#141413).
- **Every section uses `#FAF9F5` (Ivory Light) as its background — mandatory, no exceptions.** Surface variation comes from the cards placed inside sections, not from changing section backgrounds. See `colors.md` → "Section Background Rule".
- **Surface alternation is the page rhythm at the card level:** within an ivory section, cards alternate between dark editorial features and light release cards. Hard-edged transitions, no gradients, no shadow softening.
- **All cards use 24px radius** (light release, dark editorial, callout) — this is the system's signature card geometry.
- **Emphasis is typographic, not chromatic.** Underline keywords in display headlines; never colorize, glow, or highlight them.

## Module Index

### Foundation (read first for any UI work)
- [colors.md](colors.md) — all background, text, and border color tokens
- [typography.md](typography.md) — heading scale, paragraphs, labels, links
- [layout.md](layout.md) — spacing rhythm, containers, animation, visual depth
- [radius.md](radius.md) — border-radius scale
- [shadows.md](shadows.md) — elevation tokens
- [borders.md](borders.md) — border widths and styles

### Components
- [buttons.md](buttons.md) — button variants, sizes, states, asymmetric primary CTA
- [button-group.md](button-group.md) — grouped button structure
- [cards.md](cards.md) — light release cards and dark editorial feature cards
- [inputs.md](inputs.md) — form controls, labels, states
- [alerts.md](alerts.md) — alert variants
- [badges.md](badges.md) — badge variants, metadata labels
- [lists.md](lists.md) — list components
- [avatars.md](avatars.md) — avatar variants, sizes, indicators
- [icon-shapes.md](icon-shapes.md) — icon containers

### Complex Components
- [accordion.md](accordion.md) — accordion variants
- [dropdown.md](dropdown.md) — dropdown menus
- [modals.md](modals.md) — modal dialogs
- [tabs.md](tabs.md) — tab navigation
- [tables.md](tables.md) — table structure
- [pagination.md](pagination.md) — pagination components
- [sidebars.md](sidebars.md) — sidebar navigation
- [radios-checkboxes-toggle.md](radios-checkboxes-toggle.md) — selection controls
- [tooltips-popovers.md](tooltips-popovers.md) — tooltips and popovers
- [content.md](content.md) — grid system, responsiveness