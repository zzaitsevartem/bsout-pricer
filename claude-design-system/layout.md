# Layout & Spacing

## Spacing Rhythm

Base unit: **4px** (compact density). Most composition values land on a 4 / 8 / 16 / 32 / 61 / 76 / 84 grid.

| Context | Value |
|---|---|
| Section vertical padding | 84px (desktop) / 61px (tablet) / 48px (mobile) |
| Section gap (between adjacent sections) | 61px |
| Section header → content | 32px or 48px |
| Heading → paragraph | 16px |
| Container horizontal padding | 24px (desktop) / 20px (tablet) / 16px (mobile) |
| Card padding (interior) | 31px |
| Card grid gap | 16px |
| Wide component grid gap | 24px |
| Column layout gap | 32px or 48px |
| Element gap (label ↔ value, icon ↔ text) | 8px – 16px |
| Inline form gap | 12px |

## Container

Standard section container: **max-width 1200px**, centered, 24px horizontal padding.

Every major section wraps content in this container. Dark editorial feature cards do NOT extend full-bleed to the browser edge — they sit inside the 1200px column, allowing the ivory page background to peek around all four corners (the "contained inversion" effect).

## Content Composition Order

Inside each section, follow this order:
1. Heading (`h1`–`h3`)
2. Leading paragraph (subheading)
3. Normal paragraph(s)
4. Lists, CTA links, or component grids

## Section Pattern

Each section has:
- 84px vertical padding (desktop)
- **Background: `surface-page-base` (#FAF9F5, warm ivory) — mandatory, no exceptions**
- A centered container (max-width 1200px, 24px horizontal padding)
- A section header area with 32–48px bottom margin
- Section content below — typically cards placed on top of the ivory section surface

## Surface Alternation System

**Every section uses the same ivory `#FAF9F5` background.** Page rhythm is created by alternating the **cards inside sections** — not by alternating the sections themselves. See `colors.md` → "Section Background Rule" for the mandatory rule.

```
Section 1 — Ivory background (#FAF9F5)
   └─ Dark editorial feature card (#141413, radius 24px, contained in 1200px column)
Section 2 — Ivory background (#FAF9F5)
   └─ Light release card grid (#F0EEE6 / #E3DACC, radius 24px)
Section 3 — Ivory background (#FAF9F5)
   └─ Dark editorial feature card (#141413, radius 24px)
   ↓
Repeat
```

- **Ivory `#FAF9F5` is the structural baseline** — the "paper" — and it is the background for every section without exception.
- **Dark cards (#141413)** sit on the ivory section, full content-column-width but NOT viewport-edge-to-edge. The ivory section background remains visible around all four corners of the dark card. This contained inversion is essential — never let dark cards run full-bleed to the screen edges, and never use `#141413` as a section background.
- **Light release cards (#F0EEE6 or #E3DACC)** are tertiary surfaces sitting on top of the ivory section. They differentiate from the page base purely through warm tonal shift, never through borders or shadows.
- Transitions between cards are **hard-edged**. No gradient fades, no soft blends, no shadow softening.

## Card Surface Selection Rules

- Single editorial / hero feature → use the **dark feature card** (#141413, 24px radius) on top of the ivory section
- Content listings, releases, articles, blog cards → use **light cards** alternating between `surface-elevated` (#F0EEE6) and `surface-warm-card` (#E3DACC) within a grid, all sitting on top of the ivory section
- Callout / quote / pull-out → use `surface-warm-card` (#E3DACC) for warmth differentiation
- Avoid placing two dark cards adjacent to one another; rhythm requires light → dark → light alternation **at the card level**, with ivory section breathing room between each.

## Motion & Animation

- Prefer CSS-native: `transition`, `animation`, `@keyframes`. Use a Motion library only when CSS cannot achieve the behavior.
- **Transitions are short and editorial:** 120–200ms ease-out for hover/focus states. No bouncy, springy, or theatrical easings.
- **Reserve scroll-triggered animations** for moments that reinforce hierarchy (a feature card revealing on scroll). One orchestrated reveal per page is preferred over many isolated effects.
- No parallax, no auto-playing carousels, no hover wobbles. The system is editorial, not interactive-playful.
- Hover changes are color/border shifts only — no scale, no rotate, no shadow-lift.

## Backgrounds & Visual Depth

- Default to flat, warm ivory backgrounds for all page sections.
- Use **surface color contrast** (ivory ↔ warm-card ↔ slate-dark) and 1px borders for visual separation.
- **No gradient meshes, noise textures, grain overlays, or blur effects** — maintain a clean, printed-paper canvas.
- **No shadows under sections, cards, or hero blocks.**
- Every visual treatment must serve a compositional purpose (structure, separation, or emphasis). No purely ornamental effects competing with content.

## Imagery Treatment

- Use imagery sparingly — text dominates; imagery is a single dramatic accent per major section, never a repeating motif.
- Inside dark feature cards, imagery is hard-clipped to the card's 24px radius (matching the card's outer corners).
- Prefer dark-field, high-contrast 3D / scientific / abstract visualizations on dark cards (luminous lines on near-black). Avoid stock photography.
- Decorative icons should be linear, monochromatic, and sit in `heading` or `body` color — not chromatic.

## Must

- **Every section: background `#FAF9F5` (Ivory Light, `surface-page-base`) — mandatory, no exceptions.** See `colors.md` → "Section Background Rule".
- All containers: max-width 1200px, centered, 24px horizontal padding
- Vertical rhythm: 84px section padding, 61px between sections
- Card radius: 24px on every card variant (light release cards, dark feature cards, callout cards)
- Card padding: 31px on all sides
- Layouts readable and properly spaced on both desktop and mobile
- Dark feature cards always sit inside the 1200px column (never full-bleed) and never replace a section background
