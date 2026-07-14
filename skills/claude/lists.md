# Lists

> Dependencies: `colors.md`, `typography.md`

## Core Specs

- **Item spacing:** 12px vertical gap between list items (16px for spacious / reading lists)
- **Text:** Anthropic Sans 16px, weight 400, `body` color, line-height 1.5
- **Marker:** custom — replace native bullets with subtle ink markers (see Marker Styles)
- **Indent:** 0 (list aligns with surrounding text), with marker living in a 24px reserved gutter

## Marker Styles

| List type | Marker |
|---|---|
| Unordered | 3x3px square (0px radius) in `body-subtle` color, centered vertically with text |
| Ordered | Anthropic Sans numerals, weight 500, `body-subtle` color, trailing `.` separator |
| Description / definition | Term in Anthropic Sans 15px weight 600 `heading` color, definition indented 24px in `body` |
| Checklist (read-only) | 14x14px square outline in `border-default-strong`; checked items use a 14x14px filled square in `heading` with an ivory checkmark |

Native disc/circle bullets are replaced with the 3x3px square marker — preserves the 0px-radius / sharp-corner signature.

## List Icons (when icons replace markers)

- Size: 16x16px (compact lists) or 20x20px (spacious / reading lists)
- Stroke: 1.5px linear, monochromatic
- Prevent squishing: `flex-shrink: 0`
- Spacing: 8px right margin between icon and text
- Active / featured icon: `heading` color (or `fg-clay` for a single accented row — never multiple)
- Neutral icon: `body-subtle` color

## Inactive / Disabled Items

- Text: `body-muted` with `text-decoration: line-through` (decoration color matches text)
- Marker / icon: `body-muted`
- Cursor: not-allowed when interactive

## Inline / Comma-separated Lists

For tag rows or metadata lists that read as a single sentence:
- Items separated by ` · ` (interpunct) or ` — ` (em dash) in `body-muted` color
- Use Anthropic Mono if the items are categorical labels (DATE, CATEGORY)

## Description List

Used for metadata blocks (DATE / CATEGORY / AUTHOR pairs) inside cards.

- Layout: 2-column grid, term + definition rows, 16px row gap, 24px column gap
- Term: Anthropic Mono 16px, weight 400, **uppercase**, letter-spacing +0.04em, `body-muted` color
- Definition: Anthropic Sans 15px, weight 400, `heading` color
- No borders between rows; vertical rhythm carries the structure.

## Numbered Steps / Process Lists

- Marker: Anthropic Mono 14px weight 500, `body-subtle` color, uppercase numeral with leading `0` (e.g. `01.`, `02.`)
- Item heading: Anthropic Sans 18px, weight 600, `heading`
- Item body: Anthropic Sans 15px, `body`
- Step gap: 24px

## Pattern

Vertical flex list with 12px gap. Each item is a flex row with centered alignment — marker or icon (16–20px, no-shrink, 8px right margin) followed by `body`-colored text. Markers and icons inherit color from the row context, never chromatic.

## Rules

- **Replace native disc bullets** with the 3x3px square marker — preserves the system's sharp-corner language.
- **No chromatic accent colors** for list markers in default contexts. Reserve `fg-clay` for a single emphasized row, max one per list.
- **Description-list terms use Anthropic Mono uppercase** — they read as data classification labels.
- **No drop shadows** on list items.
- **No hover background fills** on read-only lists; use background-color shifts only on interactive list items (e.g. dropdown options).
