# Accordion

> Dependencies: `colors.md`, `radius.md`, `borders.md`, `typography.md`

Accordions are flat, ink-bordered, and chromeless. Triggers and panels share the warm ivory surface family — separation is created by 1px ink hairlines, never by drop shadows.

## Core Specs

- **Wrapper:** full width, 1px border `border-brand` (slate-dark), 0px radius — sharp corners on all items
- **Item separator:** 1px bottom border `border-default-subtle` on every item except last
- **Shadow:** none, ever

## Trigger (Button)

- **Layout:** flex, space-between, full width
- **Padding:** 20px horizontal, 18px vertical
- **Font:** Anthropic Sans 16px, weight 500, letter-spacing -0.002em
- **Text color:** `heading`
- **Background:** `surface-page-base` (ivory)
- **Hover:** `surface-elevated` (#F0EEE6) background
- **Focus:** outline none, 2px solid offset focus ring in `border-brand`
- **Transition:** 120–200ms ease-out on `background-color` only — never on transform
- **Open state:** `surface-elevated` background

## Panel (Content)

- **Padding:** 20px horizontal, 20px vertical
- **Background:** `surface-page-base` (ivory)
- **Top border:** 1px solid `border-default-subtle`
- **Font:** Anthropic Sans 16px, `body` color, line-height 1.5
- **Headings inside panels** use `h4`/`h5` from `typography.md`

## Chevron Icon

- Size: 16x16px
- Stroke: 1.5px linear
- Color: `body` text color (open: `heading`)
- Closed: 0deg rotation
- Open: 180deg rotation
- Transition: 150ms ease-out on transform — this is the one place transform is permitted, since the icon literally rotates

## Variants

### Default (Collapse)
One panel open at a time. Items stacked inside a single shared 1px ink-bordered wrapper with sharp corners.

### Separated Cards
Each item is independent — has its own 1px `border-brand` border, 0px radius, no shadow. 12px bottom margin between items. No shared outer border. The wrapper is transparent.

### Always Open
Multiple panels can expand simultaneously. Same styling as Default.

### Flush
No outer border. Trigger and panel have transparent backgrounds. Only 1px `border-default-subtle` bottom-border dividers between items. Use inside cards or sections that already provide a background.

## States

| State | Trigger appearance |
|---|---|
| Closed | `heading` text, `surface-page-base` background |
| Open | `heading` text, `surface-elevated` background |
| Hover | `surface-elevated` background, `heading` text |
| Focus | 2px solid offset `border-brand` ring, no outline |
| Disabled | `fg-disabled` text, not-allowed cursor, no hover/focus |

## Rules

- **0px radius mandatory** — sharp corners on wrapper, items, and separated-card variants.
- **No drop shadows.** Borders carry all separation.
- **Hover and open states use ivory tonal shifts** (`surface-page-base` → `surface-elevated`), never chromatic fills.
- **Focus rings are solid 2px offset** in `border-brand` — never a glowing ring.
- **Icon stroke matches body weight** (1.5px linear).
- Don't use accent colors (clay/sky/fig) on accordion triggers or panels.
