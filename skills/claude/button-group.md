# Button Groups

> Dependencies: `buttons.md`, `colors.md`, `radius.md`, `borders.md`

Button groups in this system are flat, sharp-cornered, and connected by overlapping 1px ink-line borders. No drop shadows, no asymmetric radius (that's reserved for the standalone Primary Nav CTA).

## Core Specs

- **Wrapper:** inline-flex, 0px radius, no shadow
- **Children overlap:** -1px left margin on all except first button (the borders share an ink line)
- **Buttons inside the group never have individual shadows.** The system uses zero shadows.
- **Borders:** every button in the group has the same border (typically 1px `border-brand`)

## Anatomy

### Wrapper
- Display: inline-flex
- Radius: 0px
- Shadow: none
- Background: transparent

### First Button
- 0px radius on all corners

### Middle Button(s)
- 0px radius on all corners

### Last Button
- 0px radius on all corners

### All buttons except the first
- -1px left margin to overlap borders so the shared ink line reads as a single continuous edge

## Active State (segmented control behavior)

When the group represents a segmented selector:
- **Active button:**
  - Background: `brand` (slate-dark)
  - Text: `surface-page-base` (ivory)
  - Border: stays 1px `border-brand`
  - The active button's z-index is raised so its full ink border sits above neighbors
- **Inactive buttons:**
  - Background: transparent or `surface-page-base`
  - Text: `heading`
  - Border: 1px `border-brand`

## Sizes

Inherit from `buttons.md` — XS / SM / Base / LG / XL. All buttons within a single group must share the same size.

## Icon-only Buttons

- 16x16px icon (1.5px stroke, monochromatic)
- Container width matches the height of text buttons in the same group (square aspect)
- 0px radius

## Rules

- Buttons inside groups follow all styles from `buttons.md` (background, border, focus rings) except they never carry **individual** drop shadows.
- **The asymmetric `0px 0px 8px 8px` Primary Nav CTA radius is forbidden inside button groups.** Groups always use uniform 0px corners.
- All buttons in a single group share size, font-weight, and border treatment — mixed-variant groups are forbidden.
- **No background gradients, no shadow lift on hover.** Hover changes background color or border color only.
- Focus rings: 2px solid offset `border-brand` ring on the focused button — the ring sits above sibling buttons via z-index.
- Maximum 5 buttons per group; beyond that, switch to a select / dropdown pattern.
