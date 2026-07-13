# Inputs

> Dependencies: `colors.md`, `radius.md`, `borders.md`, `typography.md`

## Core Specs

- **Display:** block, full width
- **Radius:** 0px (base) — sharp corners, ink-on-paper
- **Border:** 1px solid `border-default`
- **Background:** `surface-page-base` (ivory) — inputs sit on the same warm surface as the page; tonal contrast comes from the border, not a darker fill
- **Shadow:** none
- **Font:** Anthropic Sans 15px, weight 400, `heading` color
- **Padding:** 12px horizontal, 10px vertical
- **Placeholder:** `body-muted` color, weight 400
- **Caret:** `heading` color
- **Transition:** 120–200ms ease-out on `border-color` and `background-color` only — never on transform.
- **Letter-spacing:** -0.002em

## Label

- Display: block
- Font: Anthropic Sans 15px, weight 500, `heading` color
- Margin bottom: 8px
- Letter-spacing: -0.002em
- Label `htmlFor` must match the input `id`

## Helper Text / Hint

- Font: Anthropic Sans 14px, weight 400, `body-subtle` color
- Margin top: 6px
- Line-height: 1.4

## Sizes

| Size | Font size | Horizontal padding | Vertical padding |
|---|---|---|---|
| Small | 14px | 10px | 8px |
| Base (default) | 15px | 12px | 10px |
| Large | 16px | 14px | 14px |

## States

### Default
- Border: `border-default`
- Background: `surface-page-base`

### Hover
- Border: `border-default-strong`
- Background: stays `surface-page-base` — never tonal shift on hover

### Focus
- Outline: none
- Border: 1px solid `border-brand` (slate-dark)
- Focus ring: **2px solid offset** in `border-brand` (no glow, no blur, no chromatic ring)

### Filled (has value)
- Border: `border-default-strong`
- Text: `heading`

### Success
- Border: `border-success`
- Focus ring: 2px solid offset in `border-success`
- Helper text: `fg-success`

### Error / Danger
- Border: `border-danger`
- Focus ring: 2px solid offset in `border-danger`
- Helper text: `fg-danger-strong`

### Warning
- Border: `border-warning`
- Focus ring: 2px solid offset in `border-warning`

### Disabled
- Background: `disabled` (oat tone)
- Border: `border-default`
- Text: `fg-disabled`
- Cursor: not-allowed
- No hover, no focus.

### Read-only
- Background: `surface-elevated`
- Border: `border-light-subtle`
- Text: `body`
- No focus state.

## Input with Icons

- Icon size: 16x16px
- Icon stroke: 1.5px linear, monochromatic
- Icon color: `body-subtle`; on focus → `heading`
- Container: relative-positioned wrapper
- Start icon: absolutely positioned left, 12px from left edge — input gets 36px left padding
- End icon: absolutely positioned right, 12px from right edge — input gets 36px right padding
- Icons vertically centered within the wrapper

## Textarea

- Same border, radius, background, focus rules as text inputs.
- Min-height: 96px; resize vertical only.
- Padding: 12px horizontal, 10px vertical.
- Line-height: 1.5.

## Select

- Same border, radius, background, focus rules as text inputs.
- Native `<select>` chevron OR a custom 16x16px chevron icon in `body-subtle` (12px from right edge).
- Right padding: 36px to clear the chevron.

## Search Input

- Identical to text input.
- Lead with a 16x16px magnifier icon (start-icon position).
- Optional clear button (right end-icon position) appears once a value is entered: 14x14px X glyph in `body-subtle`, hover → `heading`, no background.

## File / Dropzone

- Border: 1px **dashed** `border-default-strong` (the only place dashed borders are permitted in this system)
- Background: `surface-elevated`
- Radius: 0px
- Padding: 32px
- Hover: border becomes `border-brand`, background `surface-warm-card`
- No shadow.

## Rules

- Every input must have a unique `id`
- Every input must have a matching `<label htmlFor>`
- Padding: 12px horizontal, 10px vertical (default) unless overridden for icon variants
- **0px radius is mandatory** — never round inputs (no 4px, 6px, pill).
- **Background is the ivory page base, not a darker fill.** Tonal differentiation comes from the 1px border.
- **No drop shadows on focus** — focus state is a solid 2px offset ring in `border-brand`, never a blurred glow.
- **No chromatic accent backgrounds** (no clay/sky/fig fills on inputs).
- No arbitrary hex or hardcoded colors — always reference tokens.
