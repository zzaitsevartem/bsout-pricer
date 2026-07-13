# Tables

> Dependencies: `colors.md`, `radius.md`, `shadows.md`, `borders.md`, `typography.md`

Tables are flat ledger surfaces — ink-on-paper, with hairline rules separating rows. The aesthetic borrows from broadsheet data tables: typographic rhythm carries the structure, not chromatic alternation.

## Wrapper

- Horizontal scroll overflow on small viewports
- Background: `surface-page-base` (ivory)
- Radius: 0px (base) — sharp corners on the wrapper
- Border: 1px solid `border-brand` (slate-dark) — primary ledger frame
- Shadow: none

## Table Element

- Full width, left-aligned text (right-aligned for RTL)
- Font: Anthropic Sans 15px, weight 400, `body` color
- Border-collapse: collapse
- Letter-spacing: -0.002em

## Table Head

- Font: Anthropic Sans 14px or Anthropic Mono 14px, weight 500, **uppercase**, letter-spacing +0.04em
- Color: `body-muted` for Mono header style, `heading` for Sans header style
- Background: `surface-elevated` (#F0EEE6)
- Bottom border: 1px solid `border-brand` (the broadsheet rule under the header)
- Cell padding: 16px horizontal, 12px vertical
- Sortable header arrow: 12x12px chevron in `body-muted`, hover `heading`

## Table Body

- Row background: `surface-page-base` (no zebra striping by default — the system favors hairline-only rules)
- Row bottom border: 1px solid `border-light-subtle` (omit on last row to avoid doubling with wrapper border)
- Row hover (optional): `surface-elevated` background, no transform, no shadow
- Row header (`<th scope="row">`): Anthropic Sans 15px, weight 600, `heading` color, no-wrap
- Cell padding: 16px horizontal, 14px vertical
- Cell vertical alignment: top for multi-line content, center for single-line

## Numeric / Tabular Data

- Use Anthropic Mono 14–15px for numerals, especially in financial / metric columns
- Right-align numeric columns
- `font-variant-numeric: tabular-nums` for column alignment

## Caption

- Anthropic Sans 14px, weight 400, `body-subtle` color
- Position: above the table (caption-side: top)
- Padding: 12px 0
- Used for context (e.g. "Showing 1–10 of 248")

## Sticky Header

When the table scrolls vertically:
- `<thead>` becomes `position: sticky; top: 0`
- Add a 1px bottom border `border-brand` so the rule stays visible while scrolling
- No drop shadow under the sticky header — the ink line is sufficient

## Empty State

- Caption row spanning full width
- Content: 32px vertical padding, centered Anthropic Sans 15px `body-subtle` text
- Optional small icon (24x24px linear, `body-muted`) above the message

## Compact / Dense Variant

- Reduce row padding to 8px horizontal, 8px vertical
- Font size: 14px
- Use only for data-dense interfaces (admin grids, log tables)

## Rules

- **Wrapper has horizontal scroll overflow** for responsive scrolling on small viewports.
- **Headers are uppercase Anthropic Mono** (data-classification feel) OR sentence-case Anthropic Sans 600 — pick one and apply consistently across the page.
- **No zebra striping by default.** Row separation is a hairline `border-light-subtle` only.
- **Last row omits the bottom border** to avoid doubling with the wrapper border.
- **Row headers always carry `scope="row"`** for semantic accessibility.
- **No drop shadows.** Sticky headers use the ink-line ruler, not a shadow.
- **No chromatic backgrounds for status cells.** Use Anthropic Mono uppercase tags or status badges (see `badges.md`) for state communication inside cells.
- **No arbitrary hex codes** — always reference tokens.
