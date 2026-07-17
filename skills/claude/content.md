# Content & Grid System

> Dependencies: `layout.md`, `typography.md`, `colors.md`

## Containers

| Type | Max width | Horizontal padding |
|---|---|---|
| Standard | 1200px | 24px desktop, 20px tablet, 16px mobile |
| Wide | 1280px | 24px (only for asymmetric showcases) |
| Internal (reading / long-form) | 720px | — (60–72 character line length) |
| Narrow editorial column | 560px | — (used for centered hero text columns) |

## Vertical Padding

| Breakpoint | Section vertical padding | Hero / feature padding |
|---|---|---|
| Mobile | 48px | 64px |
| Tablet (≥768px) | 61px | 76px |
| Desktop (≥1024px) | 84px | 96–120px |

## Section Gap

Adjacent sections (when not separated by a contained dark feature card) sit on a **61px gap** rhythm — never tighter than 48px, never looser than 96px without a deliberate hero context.

## Grid System

Mobile-first with flexible desktop configurations.

| Context | Gap |
|---|---|
| Standard content / cards | 16px (compact) or 24px (spacious) |
| Wide component grids | 32px |
| Compact widgets / metadata clusters | 8–12px |

### Responsive Columns

| Breakpoint | Columns |
|---|---|
| Mobile (default) | 1 |
| Small / Tablet (≥640px) | 1–2 |
| Tablet (≥768px) | 2–3 |
| Desktop (≥1024px) | 2–4 |
| Wide (≥1280px) | 3–4 |

The signature card-grid pattern is **3-column equal-width** at desktop (e.g. "Latest releases"). Two-column splits use ~55% / ~45% (the editorial hero rhythm — headline left, body or imagery right).

## Breakpoints

| Name | Width |
|---|---|
| Small | 640px |
| Medium | 768px |
| Large | 1024px |
| Extra large | 1200px |
| 2x Extra large | 1440px |

## Reading Width (long-form text)

- Body copy max-width: ~70 characters (≈ 720px at 16px Anthropic Sans)
- Heading max-width: ~30 characters at display sizes (forces line breaks at meaningful phrase boundaries)
- Pull-quote / callout max-width: ~52 characters

## Hero Column Pattern

The signature hero composition:
- Left column: large weight-700 Anthropic Sans headline (61px), spanning ~55% width
- Right column: brief descriptive paragraph at 18px Anthropic Sans, ~30% width, top-aligned with the headline baseline
- Both sit on the ivory page background with 80px top padding
- Selected keywords in the headline carry the thick-underline emphasis (see `typography.md`)

## Section Composition

Standard editorial section:
1. Optional eyebrow (Anthropic Mono 12px uppercase `body-muted`, +0.04em tracking)
2. Heading (`h2` at 40px or `h3` at 24px)
3. Leading paragraph (subheading 18px)
4. Section content (cards grid, list, or single body column)
5. CTA Arrow Text Link if applicable

## Rules

- **Always design mobile-first.** Stack columns on mobile, expand to multi-column at tablet+.
- **Use layout shifts (column → row)** to accommodate horizontal space rather than stretching components.
- **Lists:** 0–24px left indent, 12px vertical gap between items (see `lists.md`).
- **Body copy:** Anthropic Sans 16px, line-height 1.5.
- **All interactive links follow the underline-on-hover or always-underlined protocol** from `typography.md`. Keywords inside large headlines use the thick-underline-as-emphasis pattern (no color change).
- **Surface alternation:** Sections alternate between `surface-page-base` (ivory) and `surface-feature-dark` editorial cards per the rhythm in `layout.md`. Don't run two dark sections back-to-back.
- **Dark feature cards live inside the 1200px container**, never full-bleed to viewport edges.
- **Maximum 4 columns at desktop** unless the content is genuinely tabular (then use `tables.md`, not the grid system).
