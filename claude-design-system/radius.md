# Border Radius

| Token | Value | Default usage |
|---|---|---|
| base | 0px | Buttons, inputs, badges, tooltips, dropdown items, nav buttons, metadata chips |
| default | 0px | Small controls, tags, labels |
| sm | 0px | Checkboxes, tiny elements |
| md | 24px | Light release cards, content listing tiles, secondary panels |
| lg | 16px | Modal containers, sidebar inner panels |
| xl | 24px | Featured editorial cards (dark surfaces), hero feature blocks |
| primary-cta | 0px 0px 8px 8px | **Signature asymmetric radius** — flat top, rounded bottom — used **only** on the primary navigation CTA button |
| full | 9999px | Avatars, dot indicators (sparingly — pills are forbidden) |

## Rules

- **0px is the default for all interactive controls** — buttons, inputs, badges, dropdown items, nav links. Sharp corners are a deliberate formal signal of the design system.
- **Cards (all variants) use 24px radius.** Light release cards, dark editorial feature cards, and tertiary callout cards all share the same 24px outer radius — this is the system's signature card geometry.
- **Featured/editorial dark cards use 24px** to read as "contained inversions" rather than full-bleed bands. Imagery inside these cards is hard-clipped at the same 24px radius.
- **Modals use 16px** — slightly tighter than cards, more architectural than buttons.
- **The primary CTA carries the asymmetric `0px 0px 8px 8px` radius** — flat top, rounded bottom only. This pattern is reserved exclusively for the top-nav primary CTA on light surfaces. Never apply this asymmetric radius elsewhere.
- **Never round button corners uniformly** — avoid 4px, 6px, or pill buttons. The 0px button radius is a deliberate formal signature.
- **Never use arbitrary radius values** outside this scale (no 2px, 6px, 12px, 20px).
- **Radius must be consistent within each component family** — all buttons share radius, all cards share radius.
- **Same-radius clipping for nested imagery:** any image or media inside a card inherits the card's radius for hard edge alignment.
