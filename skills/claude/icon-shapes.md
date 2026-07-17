# Icon Shapes

> Dependencies: `colors.md`, `radius.md`, `borders.md`

Icon containers (the small square fills behind a feature icon) preserve the system's 0px-radius / sharp-corner language. They are flat, ink-toned, and never carry shadows or glow.

## Core Specs

- **Box sizing:** border-box
- **Icon centering:** inline-flex, centered on both axes
- **Shape:** square (0px radius) — always
- **Rounded square:** 0px radius — square is the default and only shape; reject "rounded square" as a synonym for soft corners
- **Border (when applied):** 1px solid, ink-toned (`border-brand` or `border-default`)
- **Shadow:** none, ever
- **Icon stroke:** 1.5px linear, monochromatic, never chromatic except inside the explicit color variants below
- **Icon style:** outline / linear, not filled glyphs (preserves the editorial line-art feel)

## Sizes

| Size | Container | Icon |
|---|---|---|
| XS | 24x24px | 14x14px |
| SM | 32x32px | 16x16px |
| MD | 40x40px | 20x20px |
| LG | 48x48px | 24x24px |
| XL | 56x56px | 28x28px |
| 2XL | 64x64px | 32x32px |

## Color Variants

### Default (Neutral)
- Shape: square (0px radius)
- Background: `surface-warm-card` (#E3DACC)
- Icon color: `heading`
- Border: none

### Brand (subtle ivory)
- Shape: square (0px radius)
- Background: `brand-softer` (#F0EEE6)
- Icon color: `heading`
- Border: 1px solid `border-default-subtle`

### Inverted (on light surfaces)
- Shape: square (0px radius)
- Background: `brand` (slate-dark)
- Icon color: `surface-page-base` (ivory)
- Border: none

### Outline (chromeless)
- Shape: square (0px radius)
- Background: transparent
- Icon color: `heading`
- Border: 1px solid `border-brand` (slate-dark)

### Clay Accent (sparing — one per section max)
- Shape: square (0px radius)
- Background: transparent
- Icon color: `fg-clay`
- Border: 1px solid `border-clay`

### Danger
- Shape: square (0px radius)
- Background: `danger-soft`
- Icon color: `fg-danger-strong`
- Border: 1px solid `border-danger-subtle`

### Success
- Shape: square (0px radius)
- Background: `success-soft`
- Icon color: `fg-success-strong`
- Border: 1px solid `border-success-subtle`

### Warning
- Shape: square (0px radius)
- Background: `warning-soft`
- Icon color: `fg-warning`
- Border: 1px solid `border-warning-subtle`

## On Dark Surfaces (inside dark feature cards)

Inside a dark feature card (#141413), icon shapes invert:
- Background: transparent or `surface-elevated` (light) — never another dark fill
- Icon color: `surface-page-base` (ivory)
- Border: 1px solid `border-buffer` (ivory)

## Rules

- **0px radius is mandatory.** No rounded squares (4px / 8px) or circles for icon containers.
- **No drop shadows. No glow.** Containers are flat ink shapes.
- **Linear icon style preferred** over filled glyphs.
- **One chromatic-accent icon shape per section.** Default to neutral / brand variants for repeating UI moments.
- **Icon stroke matches text weight rhythm:** 1.5px stroke for body-scale icons, never thicker than 2px.
