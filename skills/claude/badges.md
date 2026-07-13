# Badges

> Dependencies: `colors.md`, `radius.md`, `borders.md`, `typography.md`

Badges in this system are deliberately **chromeless** by default — pure typography with no chip, pill, or capsule treatment. The system favors metadata labels (DATE, CATEGORY in Anthropic Mono) over filled badges. Use filled badges sparingly and only for state communication.

## Core Specs

- **Border:** 1px (when border is used) — solid, ink-toned
- **Default radius:** 0px
- **Pill radius:** 0px (pills are explicitly forbidden in this system; treat "pill" as a synonym for the default rectangular badge)
- **Shadow:** none, ever
- **Font:** Anthropic Sans for general badges; Anthropic Mono for metadata labels (DATE, CATEGORY)
- **Letter-spacing:** +0.04em (uppercase metadata labels) or normal (sentence-case badges)

## Sizes

| Size | Font size | Horizontal padding | Vertical padding |
|---|---|---|---|
| Default (small) | 12px | 8px | 2px |
| Large | 14px | 10px | 4px |
| Metadata label (chromeless) | 16px (Mono) | 0 | 0 |

## Variants

### Metadata Label (default, no chrome)
The signature badge pattern. Used for DATE, CATEGORY, TYPE labels in card footers and content meta rows.
- **Background:** transparent
- **Border:** none
- **Text:** `body-muted` color, Anthropic Mono 16px weight 400, **uppercase**, letter-spacing +0.04em
- **Radius:** 0px (no chrome)
- **No padding.**
- Pure typographic structure — never wrap with a chip, pill, or capsule background.

### Brand (subtle)
- **Background:** `brand-softer` (#F0EEE6)
- **Border:** 1px solid `border-brand-subtle`
- **Text:** `fg-brand-strong`

### Alternative (Neutral Soft, the default filled badge)
- **Background:** `surface-page-base` (ivory)
- **Border:** 1px solid `border-default`
- **Text:** `heading`

### Gray (Neutral Medium)
- **Background:** `surface-warm-card` (#E3DACC)
- **Border:** none
- **Text:** `heading`

### Clay Accent (use sparingly — one per section max)
- **Background:** transparent
- **Border:** 1px solid `border-clay`
- **Text:** `fg-clay`
- **Note:** Clay-accent badges are decorative-emphasis only. Never use clay for status communication (use Danger instead).

### Categorical Tags (sparing use)
For thematic tags only — one accent per section max.
| Variant | Background | Border | Text |
|---|---|---|---|
| Olive | transparent | `border-olive` | `fg-olive` |
| Sky | transparent | 1px solid `sky` | `fg-sky` |
| Fig | transparent | 1px solid `fig` | `fg-fig` |
| Cactus | transparent | 1px solid `cactus` | `fg-cactus` |

### Danger
- **Background:** `danger-soft`
- **Border:** 1px solid `border-danger-subtle`
- **Text:** `fg-danger-strong`

### Success
- **Background:** `success-soft`
- **Border:** 1px solid `border-success-subtle`
- **Text:** `fg-success-strong`

### Warning
- **Background:** `warning-soft`
- **Border:** 1px solid `border-warning-subtle`
- **Text:** `fg-warning`

### Dark (inverted)
- **Background:** `brand` (slate-dark)
- **Border:** none
- **Text:** `surface-page-base` (ivory)

## Pill Badges

**Pills are explicitly forbidden.** All badges retain the 0px radius. If a designer asks for a "pill," route to the rectangular default badge — the 0px radius is a deliberate formal signature.

## Badges with Icons

- Icon size (default): 12x12px
- Icon size (large): 14x14px
- Icon stroke: 1.5px linear, monochromatic, inherits text color
- Icon spacing: 4px margin next to label

## Icon-only Badge

Square shape — equalize dimensions to 24x24px, no horizontal text padding. 0px radius preserved.

## Dismissible Badges

Badge content + a close button. The close button is a 12x12px X glyph in the same color as the badge text. Close button hover backgrounds per variant:

| Variant | Close button hover background |
|---|---|
| Metadata Label | none — text is chromeless; do not make metadata labels dismissible |
| Brand | brand-soft |
| Alternative | neutral-tertiary-soft |
| Gray | neutral-tertiary |
| Clay Accent | transparent + clay-strong text shift |
| Danger | danger-medium |
| Success | success-medium |
| Warning | warning-medium |

## Dot / Notification Badge

- Positioned absolutely: -4px top, -4px right
- Size: 8x8px, **square** shape (0px radius — never circular)
- 2px border in `border-buffer` color
- Background: `danger` (clay-ember)

## Critical Rules

- **No background fills for default metadata labels** — they are pure text.
- **Never use pill (fully-rounded) shapes.** All badges are rectangular at 0px radius.
- **Never combine multiple chromatic-accent badges in a single section.** Clay/Sky/Fig/Olive/Cactus are categorical, not combinable.
- **Status badges communicate state, not decoration.** Don't use Danger badge fill as a stylistic choice when the meaning isn't actually negative.
- **Mono-typeface metadata labels are uppercase** with +0.04em tracking — never sentence-case for DATE / CATEGORY / TYPE.
