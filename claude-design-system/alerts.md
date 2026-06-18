# Alerts

> Dependencies: `colors.md`, `radius.md`, `borders.md`, `typography.md`

Alerts communicate state — informational, success, danger, or warning. Like the rest of the system, alerts favor flat surfaces, 0px corners, and ink-line borders. No glow halos.

## Core Specs

- **Padding:** 16px (vertical) 20px (horizontal)
- **Radius:** 0px (base) — sharp corners
- **Border:** 1px solid (variant-specific)
- **Background:** soft tonal fill (variant-specific)
- **Shadow:** none, ever
- **Heading:** Anthropic Sans 16px, weight 600, variant text color
- **Body:** Anthropic Sans 15px, weight 400, line-height 1.4, variant text color
- **Icon:** 16x16px, 1.5px stroke, leading the heading; matches text color
- **Layout:** flex row — icon, content (heading + body), optional close button at trailing edge
- **Heading → body gap:** 4px
- **Icon → content gap:** 12px

## Variants

### Brand (informational, the default neutral alert)
- **Background:** `brand-softer` (#F0EEE6) — warm ivory tint
- **Border:** 1px solid `border-default`
- **Text:** `heading`
- **Icon:** info glyph in `heading` color

### Success
- **Background:** `success-soft`
- **Border:** 1px solid `border-success-subtle`
- **Text:** `fg-success-strong`
- **Icon:** check glyph in `fg-success-strong`

### Danger
- **Background:** `danger-soft`
- **Border:** 1px solid `border-danger-subtle`
- **Text:** `fg-danger-strong`
- **Icon:** alert glyph in `fg-danger-strong`

### Warning
- **Background:** `warning-soft`
- **Border:** 1px solid `border-warning-subtle`
- **Text:** `fg-warning`
- **Icon:** warning glyph in `fg-warning`

### Inverted (on dark surfaces — used inside dark feature cards)
- **Background:** transparent
- **Border:** 1px solid `border-buffer` (ivory)
- **Text:** `surface-page-base` (ivory)
- **Icon:** matching ivory tone

## With Action / CTA

- CTA appears below the alert body (or trailing the body on a single line) using the **Arrow Text Link** pattern from `buttons.md` (e.g. `View details →`).
- Never use a filled brand button inside an alert — the alert itself is the emphasis surface.

## Dismissible Alert

- Trailing 16x16px X glyph button in the variant text color
- Hit area 24x24px
- Hover: subtle background tint shift (no separate close-button background fill)
- Focus: 2px solid offset focus ring in the variant border color

## Rules

- **0px radius mandatory.** Never round alerts.
- **No shadow.** Border + soft tonal fill is the entire visual signal.
- **No icon-only alerts** — always pair the icon with a heading or body text for accessibility.
- **One alert per region.** Don't stack three alerts on top of each other; consolidate or use a notification list pattern.
- **Don't use chromatic accent colors (clay/sky/fig/olive/cactus) for alert backgrounds.** Variants are restricted to the status palette + brand-softer.
- **Inverted alerts** appear only when nested inside a dark feature card — their borders use ivory, not slate-dark.
