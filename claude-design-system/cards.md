# Cards

> Dependencies: `colors.md`, `radius.md`, `shadows.md`, `borders.md`, `typography.md`, `layout.md`

Cards are the primary content container in the system. There are **two distinct card families**: light release/listing cards and the signature dark editorial feature card. Choosing the right family is a hierarchy decision, not a style decision.

## Universal Specs

- **Shadow:** none. Always. Surface contrast is the only depth signal.
- **Border:** 0px (no border on cards) — surface color separation is sufficient.
- **Padding:** 31px on all sides (matches the layout system's card-padding rhythm).
- **Internal radius alignment:** any media (images, illustrations) inside a card is hard-clipped to the card's outer radius for flush corners.

## Light Release Card (default content listing)

The standard 3-column "Latest releases" tile. Used for articles, blog posts, news, content listings.

- **Background:** `surface-elevated` (#F0EEE6) **or** `surface-warm-card` (#E3DACC) — alternate within a grid for warmth variation.
- **Radius:** 24px
- **Padding:** 31px
- **Border:** none
- **Shadow:** none
- **Heading:** Anthropic Sans, 20px, weight 600, `heading` color
- **Body text:** Anthropic Sans, 15px, weight 400, `body` color, line-height 1.4
- **Footer metadata row:** label in Anthropic Mono 16px uppercase `body-muted` color, value in Anthropic Sans 15px `heading` color
- **CTA link:** Arrow Text Link pattern (e.g. `Read announcement →`) — see `buttons.md`
- **Internal vertical rhythm:** 16px between heading and body, 24px between body and footer/CTA

### Light card states
- **Static (non-interactive):** No hover styles. Surface color and content do all the work.
- **Interactive (clickable card / link card):**
  - Hover: surface shifts one step (e.g. `surface-elevated` → `surface-warm-card`)
  - Cursor: pointer
  - Transition: 120–200ms ease-out on background-color only
  - **No transform, no scale, no shadow, no border appearance on hover.**
- **Focus (keyboard):** 2px solid offset focus ring in `border-brand` (slate-dark) wrapping the entire card

## Dark Editorial Feature Card (signature inversion)

The big editorial breakpoint that punctuates the page rhythm. Used for hero features, project announcements, pillar content moments. **One per major section, max two per page.**

- **Background:** `surface-feature-dark` (#141413)
- **Radius:** 24px
- **Padding:** 31px (or 48px+ on hero-scale variants)
- **Border:** none
- **Shadow:** none — the card sits flush in the layout grid; the radius IS the visual signal
- **Width behavior:** **Full content-column-width within the 1200px container — never full-bleed to viewport edges.** The ivory page background must remain visible around all four corners (the "contained inversion").
- **Headline:** Anthropic Serif, 91px (display) on desktop, weight 400, `surface-page-base` (ivory) color, line-height 1.10
  - Mobile: 48–56px
  - **This is the only place Anthropic Serif at display scale appears in the system.**
- **Subheading / body:** Anthropic Sans, 18–20px, weight 400, `body-subtle` mapped to its dark-surface value (light ivory tone)
- **CTA button:** Primary on-dark variant — see `buttons.md` (ivory fill, slate-dark border, 0px radius)
- **Embedded imagery:** hard-clipped to 24px radius matching the outer card, typically a dark-field 3D / scientific visualization with luminous lines
- **Layout:** typically split-column — headline + CTA on left ~55%, imagery on right ~45%

### Dark card states
- **Static (non-interactive):** No hover. The card is a content surface, not an action.
- **Interactive (rare — only when the entire card is a link):** Subtle imagery zoom (1.0 → 1.02) clipped at the 24px radius, OR a subtle text-color shift on the embedded CTA. **Never** a background brightness change — the slate-dark surface is fixed.
- **Focus:** 2px solid offset focus ring in `border-buffer` (ivory) — visible against the dark surface

## Tertiary Surface Card (callout / quote / pull-out)

For block quotes, callouts, sidebar excerpts, single-stat blocks.

- **Background:** `surface-warm-card` (#E3DACC)
- **Radius:** 24px
- **Padding:** 31px
- **No border, no shadow.**
- **Heading:** Anthropic Sans, 24px, weight 600, `heading` color
- **Body / quote text:** Anthropic Sans, 16–18px, `body` color
- Used to break long-form light card grids with a tonal warmth shift.

## Card Heading Hierarchy

- The page hierarchy must logically arrive at the card heading level — never skip from `h1` to a `h4` card heading.
- Light cards typically host an `h3` (24px) or `h4` (20px) heading.
- Dark editorial cards host an `h2` (Anthropic Serif 91px, mapped to display) — they are display-scale moments.
- Tertiary callout cards host an `h4` or `h5`.

## Rules

- **Background:** `surface-elevated` / `surface-warm-card` for light cards; `surface-feature-dark` for editorial feature cards.
- **Border:** none on cards.
- **Radius:** **24px on every card variant** — light release cards, dark editorial feature cards, and tertiary callout cards all share the same 24px outer radius. This is the system's signature card geometry.
- **Shadow:** **none, ever, on any card.**
- **Text color:** `heading` and `body` on light cards; ivory (`surface-page-base`) and `body-subtle` mapped to dark on dark feature cards.
- **Interactive light cards:** background-color shift on hover only (no transform / shadow / scale / border).
- **Non-interactive cards:** no hover styles.
- **Dark feature cards never run full-bleed to the viewport edge** — they sit inside the 1200px column with ivory peeking around all corners.
- **One dark feature card per section maximum**, and never two adjacent dark sections (alternation rule from `layout.md`).
- **Imagery clips to card radius:** 24px on all card variants — interior images, illustrations, and media are hard-clipped to match the card's 24px outer corners.
- **Never combine multiple chromatic accents inside a single card** — the underlying palette is achromatic.
