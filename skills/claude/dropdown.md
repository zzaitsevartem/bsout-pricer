# Dropdown

> Dependencies: `colors.md`, `radius.md`, `shadows.md`, `borders.md`, `inputs.md`, `typography.md`

Dropdowns are floating, transient overlays — one of the few places a subtle drop shadow is permitted (`shadow-overlay`). The trigger button itself remains flat with 0px corners and an ink-line border.

## Core Specs

### Chevron Icon
- Size: 16x16px
- Stroke: 1.5px linear, monochromatic
- Spacing: 8px left margin from label, -2px right inset
- Color: inherits from trigger text

### Menu Container
- Background: `surface-page-base` (ivory)
- Border: 1px solid `border-brand` (slate-dark)
- Radius: 0px (base)
- Shadow: `shadow-overlay` (the only shadow allowed on this surface — it floats over content)
- Z-index: elevated above content
- Margin top: 8px from trigger

### Menu List
- Padding: 8px
- Font: Anthropic Sans 15px, weight 400, `body` color

### Menu Item
- Layout: inline-flex, vertically centered, full width
- Padding: 10px horizontal, 8px vertical
- Radius: 0px
- Background: transparent
- Text: `body`
- Hover: `surface-elevated` (#F0EEE6) background, `heading` text
- Transition: 120–200ms ease-out on `background-color` and `color` only

## Trigger

The trigger is a button — see `buttons.md`. Common pairings:
- Ghost / nav trigger (transparent, 1px slate-dark border, 0px radius)
- Tertiary trigger (1px `border-default`)
- Input-style trigger when used as a select replacement

## Trigger Sizes

| Size | Font size | Horizontal padding | Vertical padding |
|---|---|---|---|
| Small | 14px | 12px | 8px |
| Base | 15px | 16px | 10px |
| Large | 16px | 20px | 12px |

## Icon-only Trigger

- Padding: 8px
- Min size: 44x44px
- Icon: 20x20px, 1.5px stroke
- Background: transparent
- Border: 1px `border-default` (or `border-brand` for the primary variant)
- Hover: `surface-elevated` background

## Variants

### Default
- Menu min-width: 192px, items have 0px radius

### With Divider
- 1px top border `border-default-subtle` between child groups (skip the first group)
- 4px vertical margin around the divider

### With Header
- Header padding: 12px horizontal, 12px vertical
- Bottom border: 1px `border-default-subtle`
- Name: `heading` color, Anthropic Sans 15px, weight 600
- Email / subtitle: `body-subtle` color, Anthropic Sans 14px, weight 400, truncated

### With Icons
- Icon before label: 16x16px, 8px right margin, `body-subtle` color, 1.5px stroke
- On hover, icon color shifts to `heading`

### With Checkbox / Radio
- Inputs: 16x16px square (0px radius — see `radios-checkboxes-toggle.md`)
- Focus ring: 2px solid offset `border-brand`
- Helper text: Anthropic Sans 12px, `body-subtle` color, 4px top margin

### With Search
- Search input at top of menu following `inputs.md` specs
- Left magnifier icon: 12px from left edge, input gets 36px left padding
- Search input border: 1px `border-default-subtle` (lighter than menu's outer border)

### Scrollable
- Max height: 224px (≈ 6 standard items), vertical scroll overflow
- Custom scrollbar: 8px wide, `border-default` thumb, transparent track

## States

| State | Appearance |
|---|---|
| Focused trigger | No outline, 2px solid offset focus ring in `border-brand` |
| Hover item | `surface-elevated` background, `heading` text |
| Active / selected item | `surface-warm-card` background, `heading` text, optional 1px left bar in `border-brand` |
| Disabled item | `fg-disabled` text, not-allowed cursor, no pointer events, no hover background |

## Rules

- **0px radius on the menu container, items, and trigger.** No soft corners.
- **`shadow-overlay` is permitted only on the floating menu surface.** The trigger button never carries a shadow.
- **Hover backgrounds are warm tonal shifts** (ivory → elevated → warm-card), never chromatic.
- **No accent colors as menu item backgrounds.** Selected state uses the warm-card surface, not a brand fill.
- **Focus rings are solid 2px offset** in `border-brand` — never a glowing ring.
- **Icon stroke 1.5px linear** for all menu icons.
