# Tabs

> Dependencies: `colors.md`, `radius.md`, `shadows.md`, `borders.md`, `typography.md`

Tabs are flat, ink-bordered, sharp-cornered. Active state is communicated through ink-line emphasis (a thicker bottom border or a slate-dark fill), never through chromatic accents or glow.

## Core Specs

- **Typography:** Anthropic Sans 15px, weight 500 (active), 400 (inactive), `body` color
- **Transitions:** 120–200ms ease-out on `color`, `background-color`, `border-color` only — never on transform

## Variants

### 1. Underline (Default — the editorial pattern)

**Wrapper:** bottom border 1px solid `border-default-subtle`

**Tab Item:**
- Padding: 16px horizontal, 14px vertical
- Bottom border: 2px solid transparent (reserves space so active state doesn't shift layout)
- Top corners: 0px radius
- Transition: 150ms ease-out on `color` and `border-color`

| State | Appearance |
|---|---|
| Active | `heading` text, 2px solid `border-brand` bottom border (slate-dark) |
| Inactive | `body` text, transparent bottom border; hover → `heading` text, 2px `border-default-strong` bottom border |
| Disabled | `fg-disabled` text, not-allowed cursor, transparent bottom border |
| Focus | 2px solid offset focus ring in `border-brand` — does NOT replace the bottom-border indicator |

### 2. Pills (sharp-cornered, not actually pill-shaped)

Note: "Pills" is the convention name; in this system the pill radius is **0px** (sharp). The variant exists for a contained, button-like tab cluster, not a fully-rounded shape.

**Tab Item:**
- Padding: 16px horizontal, 10px vertical
- Radius: 0px (base)
- Font weight: 500 (active), 400 (inactive)
- Transition: 150ms ease-out

| State | Appearance |
|---|---|
| Active | `brand` background (slate-dark), `surface-page-base` text (ivory), no shadow |
| Inactive | transparent background, `body` text; hover → `surface-elevated` background, `heading` text |
| Disabled | `fg-disabled` text, not-allowed cursor |
| Focus | 2px solid offset focus ring in `border-brand` |

### 3. Full Width (segmented bar)

Children overlap with -1px left margin on all except first (shared ink-line border).

**Tab Item:**
- Full width, centered text
- Padding: 14px horizontal, 14px vertical
- Background: `surface-page-base` (ivory)
- Border: 1px solid `border-brand`
- Radius: 0px on every corner of every child — uniformly sharp
- Transition: 150ms ease-out on `background-color` and `color`
- Hover: `surface-elevated` background, `heading` text

| State | Appearance |
|---|---|
| Active | `brand` background, `surface-page-base` text (ivory), 1px `border-brand` |
| First item | sharp start (0px) |
| Last item | sharp end (0px) |
| Focus | 2px solid offset focus ring in `border-brand`, raised z-index |

## Tabs with Icons

- Icon size: 16x16px (default) or 20x20px (large tabs)
- Stroke: 1.5px linear, monochromatic
- Spacing: 8px right margin between icon and label
- Layout: inline-flex, vertically centered
- Icons inherit the text color of the tab state — no chromatic icon colors

## Tab Panel

- Background: transparent (or `surface-page-base` if the surrounding surface is dark)
- Padding: 24px top, 0 horizontal (panel content uses its own container padding)
- Top margin: 0 (the underline / bar carries the visual edge)

## Rules

- **0px radius** across all tab variants — no pill-rounded tabs.
- **Active state is signaled by ink-line emphasis** (slate-dark bottom border or slate-dark background), never by clay/sky/fig accent colors.
- **No drop shadows** on tab wrappers or items.
- **Focus rings are 2px solid offset** in `border-brand`, never glowing.
- **Transitions on color and border only** — never on transform or shadow.
- Don't use chromatic accents to indicate active tabs.
