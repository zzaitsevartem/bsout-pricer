# Sidebars

> Dependencies: `colors.md`, `radius.md`, `borders.md`, `typography.md`, `badges.md`, `alerts.md`

Sidebars in this system are flat, ink-bordered, and quietly editorial. They use the warm ivory family — never a darker chrome fill — and rely on 1px hairlines for separation.

## Core Specs

- Background: `surface-page-base` (ivory, #FAF9F5) — same surface as the main page (sidebars don't visually "lift")
- Right border: 1px solid `border-default-subtle` (left-sidebar); left border for right-sidebar
- Width: 264px (default) — generous breathing room for editorial-feel nav
- Min-width: 240px on tablet
- Shadow: none

## Anatomy

### Outer Container
Hidden on mobile (<768px), visible on tablet+. Needs a toggle / trigger for mobile (hamburger button in the top-nav).

### Inner Wrapper
- Full height, vertical scroll overflow
- Padding: 16px horizontal, 24px vertical

### Sidebar Header / Wordmark
- Padding: 8px horizontal, 16px vertical
- Wordmark: Anthropic Sans 16px, weight 700, `heading` color
- Optional eyebrow: Anthropic Mono 12px uppercase, +0.04em tracking, `body-muted`

### Navigation Section Title
- Anthropic Mono 12px, weight 400, **uppercase**, +0.04em tracking, `body-muted`
- Top margin: 16px, bottom margin: 8px
- Padding: 0 8px

### Navigation List
- Vertical spacing: 4px between items
- Font: Anthropic Sans 15px, weight 400 (inactive), 500 (active)

### Navigation Item
- Layout: flex, vertically centered
- Padding: 10px horizontal, 8px vertical
- Text: `body` color (inactive), `heading` (active)
- Radius: 0px (base)
- Border: 0
- Hover: `surface-elevated` (#F0EEE6) background
- Transition: 120–200ms ease-out on `background-color` and `color` only
- Icon: 16x16px (default) or 20x20px (large), 1.5px linear stroke, `body-subtle` (inactive), `heading` (hover/active)
- Label: 12px left margin from icon
- Trailing badge / count: see `badges.md` (right-aligned)

### Active Item
- Background: `surface-elevated` or `surface-warm-card` (one step warmer than the sidebar surface)
- Text: `heading` color
- Optional 1px left bar in `border-brand` (slate-dark, 2px wide, full item height) — the editorial mark for "this is where you are"
- No chromatic accent fill, no glow

### Separator
- 16px top padding, 16px top margin
- Top border: 1px solid `border-default-subtle`
- 8px vertical spacing below

### Multi-level / Nested Items
- Child indent: 28px left padding
- Same hover / active treatment as top-level items
- Disclosure chevron: 12x12px, 0deg (collapsed) → 90deg (expanded), 150ms ease-out transform on the chevron only

### Bottom CTA / Card
- Padding: 16px
- Top margin: 24px
- Radius: 24px (matches the system's unified card radius)
- Background: `surface-warm-card` (#E3DACC) — warm tonal step from the page base
- Can also use any alert variant from `alerts.md`
- Heading: Anthropic Sans 15px weight 600 `heading`
- Body: Anthropic Sans 14px `body`
- CTA: Arrow Text Link pattern from `buttons.md`

## Collapsed / Mini Sidebar

- Width: 64px
- Items show icon only (20x20px, centered)
- Tooltip on hover (see `tooltips-popovers.md`)
- Wordmark collapses to a square mark
- All other rules unchanged

## Right-side / Detail Sidebar

- Same specs but mirrored — left border instead of right border
- Often used for table-of-contents, in-page navigation: link items use `body` color with 2px left `border-default-subtle` rule that becomes `border-brand` on the active item

## Rules

- **Background matches the page surface** (`surface-page-base`) so the sidebar feels like a continuation of the canvas, not a separate panel.
- **0px radius on nav items.** No soft-cornered nav rows.
- **Active state uses warm tonal step + 2px slate-dark left bar**, never chromatic accent backgrounds.
- **No drop shadows** on the sidebar or its items.
- **Icons are 1.5px linear strokes**, monochromatic, inheriting text color.
- **No transform on hover.** Background-color + color shift only.
- **Multi-level menus indent with 28px** (one base unit cluster), not 44px.
- **Spacing follows the 4 / 8 / 16 / 24 / 32 rhythm.**
- **Only neutral / brand / status / clay tokens** — clay used sparingly (max one accent indicator across the entire sidebar).
- Responsive: hidden on mobile with a hamburger toggle in the top-nav.
