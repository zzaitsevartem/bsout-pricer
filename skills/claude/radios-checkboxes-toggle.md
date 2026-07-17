# Radios, Checkboxes & Toggles

> Dependencies: `colors.md`, `radius.md`, `borders.md`, `typography.md`

Selection controls in this system stay flat, sharp-cornered, and ink-toned. Both radios and checkboxes use **square** shapes (0px radius) — the round-radio convention is replaced with a square-with-dot indicator to preserve the system's formal sharp-corner language.

## Checkbox

- Size: 18x18px
- Radius: 0px
- Border: 1px solid `border-default-strong`
- Background: `surface-page-base` (ivory)
- Hover: `border-brand`, background stays
- Focus: outline none, 2px solid offset focus ring in `border-brand`
- Transition: 120–200ms ease-out on `background-color` and `border-color`

### Checked
- Background: `brand` (slate-dark)
- Border: `border-brand`
- Indicator: 12x12px ivory check glyph, 1.5px stroke

### Indeterminate
- Background: `brand`
- Indicator: 10x2px ivory horizontal bar (centered)

### Disabled
- Background: `disabled` (oat tone)
- Border: 1px `border-default`
- Indicator (if checked): `fg-disabled` color
- Cursor: not-allowed

## Radio (square indicator — see Critical Rules)

- Size: 18x18px
- Radius: 0px (sharp — see rationale at bottom)
- Border: 1px solid `border-default-strong`
- Background: `surface-page-base` (ivory)
- Hover: `border-brand`
- Focus: outline none, 2px solid offset focus ring in `border-brand`
- Transition: 120–200ms ease-out

### Checked
- Border: 1px `border-brand`
- Background: `surface-page-base`
- Indicator: 8x8px **square** filled in `brand` (slate-dark), centered with 4px padding from outer edges

### Disabled
- Border: `border-default`
- Indicator (if checked): `fg-disabled` color
- Cursor: not-allowed

Group all radio items under the same `name` attribute. Use `aria-label` or visible label.

## Toggle (Switch)

A horizontal switch — sharp-cornered, ink-bordered.

### Track
- Width: 36px, Height: 20px
- Radius: 0px (square track)
- Background: `surface-page-base`
- Border: 1px solid `border-default-strong`
- Focus-within: outline none, 2px solid offset focus ring in `border-brand`
- Checked track: `brand` (slate-dark) background, `border-brand` border
- Disabled track: `disabled` background, `border-default`
- Transition: 150ms ease-out on `background-color`

### Thumb
- Size: 14x14px
- Radius: 0px (square thumb)
- Background: `surface-page-base` (ivory) when track is dark; `brand` (slate-dark) when track is ivory (unchecked state)
- Border: 1px `border-brand`
- Position: 2px inset from track edge; translates left↔right on toggle
- Transition: 150ms ease-out on transform — this is the one place transform is permitted (the thumb literally translates)

### Disabled
- Track: `disabled` background, `border-default` border
- Thumb: `body-muted` fill, `border-default` border
- Label: `fg-disabled`

## Label & Helper Text

- Label position: right of the control, 8px gap, vertically centered with the control
- Label font: Anthropic Sans 15px, weight 400, `heading` color
- Helper text: Anthropic Sans 14px, `body-subtle`, 4px below the label, full row indent (label gutter aligned)
- Disabled label: `fg-disabled`

## Sizes

| Size | Checkbox / Radio | Toggle Track | Toggle Thumb |
|---|---|---|---|
| Small | 14x14 | 28x16 | 10x10 |
| Base | 18x18 | 36x20 | 14x14 |
| Large | 22x22 | 44x24 | 18x18 |

## Critical Rules

- **All selection inputs must have `id` matching label `htmlFor`.**
- **Squares everywhere.** Checkboxes, radios, and toggle thumbs/tracks are 0px radius. The radio-as-square is intentional and matches the system's hard-corner formal signature; the checked indicator is a smaller filled square, not a circle.
- **No drop shadows. No glow rings.** Focus uses a solid 2px offset `border-brand` ring — never a soft halo.
- **No chromatic accents on indicators.** Checked state uses `brand` (slate-dark), never clay/sky/fig fills.
- **Transitions on color and border only**, except for the toggle thumb which uses transform (translate) for the slide.
- **Disabled states: no hover/focus interaction.**
- **Label always present** for accessibility — visually hidden labels (`sr-only`) are acceptable when the control is in a tightly contextualized cluster.
