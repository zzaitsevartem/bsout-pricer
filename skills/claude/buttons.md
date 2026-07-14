# Buttons

> Dependencies: `colors.md`, `radius.md`, `shadows.md`, `borders.md`, `typography.md`

## Core Specs (every button except ghost and disabled)

- **Radius:** 0px (base) — all buttons use sharp corners. The only exception is the **Primary Nav CTA**, which uses the asymmetric `0px 0px 8px 8px` (flat top, rounded bottom) signature.
- **Border:** 1px solid (most variants carry a 1px ink-line border on the ivory surface)
- **Shadow:** none — buttons rely on solid fills, borders, and color shifts for state. Never add box-shadow.
- **Font:** Anthropic Sans
- **Font weight:** 500 (medium) for primary / CTA buttons; 400 (regular) for ghost / nav links
- **Box sizing:** border-box
- **Transition:** 120–200ms ease-out on `color`, `background-color`, `border-color` only — never on transform or shadow.
- **Letter-spacing:** -0.002em on label text

## Sizes

| Size | Font size | Horizontal padding | Vertical padding |
|---|---|---|---|
| Extra small | 12px | 12px | 6px |
| Small | 14px | 16px | 8px |
| Base (default) | 15px | 31px | 12px |
| Large | 16px | 31px | 14px |
| Extra large | 16px | 32px | 18px |

The base button uses 31px horizontal padding to match the card padding rhythm.

## Variants

### Primary Nav CTA (the "Try Claude" button)
- **Background:** `surface-page-base` (ivory, #FAF9F5)
- **Border:** 1px solid `border-brand` (slate-dark, #141413)
- **Radius:** **`0px 0px 8px 8px`** — signature asymmetric (flat top, rounded bottom). This radius is reserved for this single CTA and never used elsewhere.
- **Text:** `heading` color (slate-dark)
- **Padding:** 12px 31px
- **Font:** Anthropic Sans 15px, weight 500
- **Hover:** `surface-elevated` background, border stays slate-dark
- **Focus:** 2px solid offset focus ring in `border-brand`, no glow
- **Active:** `neutral-secondary` background

### Primary (on dark surfaces — "Continue Reading" inside dark feature cards)
- **Background:** `surface-page-base` (ivory, #FAF9F5)
- **Border:** 1px solid `border-brand` (slate-dark)
- **Radius:** 0px (no asymmetric radius on dark surfaces)
- **Text:** `heading` color (slate-dark)
- **Padding:** 12px 31px
- **Font:** Anthropic Sans 15px, weight 500
- **Hover:** Slight transparency shift or subtle ivory→cloud-light fill swap
- **Focus:** 2px solid offset focus ring in `border-buffer` (ivory)

### Brand (high-emphasis primary on light surfaces)
- **Background:** `brand` (slate-dark, #141413)
- **Border:** 1px solid `border-brand` (slate-dark — visually flush with fill)
- **Text:** `surface-page-base` (ivory)
- **Radius:** 0px
- **Hover:** `brand-strong` background (slightly deeper near-black)
- **Focus:** 2px offset solid focus ring in `border-brand`

### Secondary (Ghost Nav Button — transparent with ink border)
- **Background:** transparent
- **Border:** 1px solid `border-brand` (slate-dark)
- **Text:** `heading`
- **Radius:** 0px
- **Padding:** 22px 12px (taller, narrower — matches inline nav rhythm) for nav usage; 12px 24px for general use
- **Font:** Anthropic Sans 15px, weight 400
- **Hover:** `surface-elevated` background fill, border stays
- **Focus:** 2px solid offset focus ring in `border-brand`

### Tertiary (subtle outline)
- **Background:** transparent
- **Border:** 1px solid `border-default`
- **Text:** `body`
- **Radius:** 0px
- **Hover:** `surface-elevated` background, `border-brand` border, `heading` text
- **Focus:** 2px solid offset ring in `border-brand`

### Ghost (no border, no background)
- **Background:** transparent
- **Border:** transparent
- **Text:** `heading`
- **Radius:** 0px
- **Hover:** `surface-elevated` background, no border appears
- **Focus:** 2px solid offset focus ring in `border-brand`
- **No shadow.**

### Arrow Text Link (the "Read announcement →" pattern)
- **Background:** none
- **Border:** none
- **Text:** `heading` color, Anthropic Sans 15px, weight 400
- **Radius:** none — pure typographic link
- **Trailing arrow:** Append literal `→` glyph directly after text label with one space.
- **No underline at rest.** On hover, an underline appears beneath the text only (not the arrow).
- **Focus:** 2px solid offset focus ring in `border-brand` wrapping the text
- Used inside cards for "Read announcement →", "Read the story", "Model details".

### Muted Ghost (de-emphasized / inactive)
- **Background:** transparent
- **Border:** 1px solid `border-default` (cloud-medium)
- **Text:** `body-muted` color
- **Radius:** 0px
- **Font:** Anthropic Sans 15px, weight 400
- **Hover:** no change OR slight border shift to `border-default-strong`
- Used for de-emphasized or inactive interactive elements.

### Success
- **Background:** `success` (olive)
- **Border:** transparent
- **Text:** `surface-page-base` (ivory)
- **Hover:** `success-strong` background
- **Focus:** 2px solid offset focus ring in `border-success`

### Danger
- **Background:** `danger` (clay-ember)
- **Border:** transparent
- **Text:** `surface-page-base` (ivory)
- **Hover:** `danger-strong` background
- **Focus:** 2px solid offset focus ring in `border-danger`

### Warning
- **Background:** `warning`
- **Border:** transparent
- **Text:** `heading` (slate-dark)
- **Hover:** `warning-strong` background
- **Focus:** 2px solid offset focus ring in `border-warning`

### Disabled (NO shadow)
- **Background:** `disabled` (oat)
- **Border:** 1px solid `border-default`
- **Text:** `fg-disabled`
- **Cursor:** not-allowed
- **No hover, no focus, no shadow.**

## Icons in Buttons

- Icon size: 16x16px
- Icon stroke: 1.5px linear, monochromatic, inherits text color (never chromatic)
- Spacing: 8px gap between icon and label
- Layout: inline-flex, vertically centered
- Trailing arrows on text links use a literal `→` glyph (not an SVG) so they share the type rhythm.

## Critical Rules

- **0px radius is mandatory for all buttons** except the Primary Nav CTA (`0px 0px 8px 8px`).
- **Never apply uniform soft corners to buttons.** No 4px, 6px, or pill rounding.
- **Never add a drop-shadow or hover lift.** State changes are color/border only.
- **Never use accent colors (clay/sky/olive/fig) as button background fills** outside the explicit Success/Danger/Warning intents. The clay accent is reserved for sparing highlight moments — not a primary CTA color.
- **The asymmetric radius is a single-button signature.** Use it only on the top-nav primary CTA.
