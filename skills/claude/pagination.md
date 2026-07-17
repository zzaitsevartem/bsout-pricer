# Pagination

> Dependencies: `colors.md`, `radius.md`, `borders.md`, `typography.md`

Pagination is a connected row of sharp-cornered ink-bordered tiles — visually a segmented control. Active state uses ink fill (slate-dark), never chromatic accents.

## Container

- Layout: inline-flex, items overlap with -1px left margin (shared ink-line border)
- Font: Anthropic Sans 14px, weight 400, `body` color
- Letter-spacing: -0.002em
- Gap: 0 (border overlap creates the rhythm)

## Pagination Item

- Layout: flex, centered both axes
- Size: 36x36px (default) or 40x40px (large)
- Text: `body` color, weight 500
- Background: `surface-page-base` (ivory)
- Border: 1px solid `border-default`
- Radius: 0px (mandatory)
- Hover: `surface-elevated` background, `heading` text, border stays
- Focus: outline none, 2px solid offset focus ring in `border-brand`, raised z-index
- Overlap: -1px left margin (except first item)
- Transition: 120–200ms ease-out on `background-color` and `color`

## Previous / Next Buttons

- Horizontal padding: 12px, height: 36px
- Icon (chevron-left / chevron-right): 14x14px, 1.5px stroke, inherits text color, 6px gap from label (when "Previous" / "Next" labels are visible)
- First item: 0px radius (always sharp)
- Last item: 0px radius (always sharp)
- Disabled state (e.g. "Previous" on first page): `body-muted` text, `border-default-subtle` border, `surface-elevated` background, no hover, not-allowed cursor

## Active Page Item

- Text: `surface-page-base` (ivory)
- Background: `brand` (slate-dark, #141413)
- Border: 1px solid `border-brand`
- Hover: stays the same (active tile doesn't react to hover) — pointer cursor remains for accessibility
- Z-index raised so its full ink border sits above neighbors
- No drop shadow

## Ellipsis ("…") Placeholder

- Same 36x36 dimensions as items
- Background: transparent
- Border: 1px `border-default`
- Text: `body-muted`, Anthropic Sans 14px weight 400
- Not interactive (no hover, no focus, no click)

## Compact Variant

For dense interfaces or footers:
- Replace numeric tiles with "Page X of Y" Anthropic Sans 14px `body` text between Previous / Next buttons
- Previous / Next remain as bordered 36x36 buttons

## Rules

- **0px radius mandatory** — no soft corners, no pills.
- **Active page uses slate-dark fill + ivory text**, never `fg-clay` or accent colors.
- **No drop shadows** on items, container, or hover state.
- **No transform on hover.** State change is `background-color` + `color` + `border-color` only.
- **Focus ring is a 2px solid offset** in `border-brand` — never a soft glow.
- **All items need hover, focus, and disabled states.**
- **Don't space items apart with gap.** The connected ink-line look (-1px overlap) is the system's signature.
