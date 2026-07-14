# Avatars

> Dependencies: `colors.md`, `radius.md`, `borders.md`, `typography.md`

Avatars in this system are **square** by default, mirroring the 0px-radius signature of buttons and badges. Circular avatars are available but reserved for chat / messaging contexts where the conversational pattern is well-established.

## Core Specs

- **Default shape:** square (0px radius) — matches the system's sharp-corner signature
- **Optional shape:** circular (full radius) — chat/messaging contexts only
- **Default size:** 40x40px
- **Image fit:** cover
- **Background (initials variant):** `surface-warm-card` (#E3DACC) with `heading` color text
- **Border (when applied):** 1px solid, ink-toned

## Sizes

| Size | Dimensions | Radius (square default) |
|---|---|---|
| Extra Small | 20x20px | 0px |
| Small | 24x24px | 0px |
| Base | 32x32px | 0px |
| Default | 40x40px | 0px |
| Large | 48x48px | 0px |
| XL | 56x56px | 0px |
| 2XL | 64x64px | 0px |

## Initials Avatar (no image)

- Background: `surface-warm-card` (#E3DACC) for warm tone, OR `brand` (slate-dark) for inverted contrast
- Text: `heading` (on warm) or `surface-page-base` (on dark)
- Font: Anthropic Sans, weight 500, size scales with avatar (e.g. 32x32px avatar → 14px initials)
- Letter-spacing: -0.002em
- Maximum 2 letters

## Bordered Avatar

- 4px padding gutter inside a 1px solid `border-brand` (slate-dark) outline
- Alternative: 2px solid `border-default` ring directly on the avatar edge
- Radius: 0px (square)
- No box-shadow — the ink line is the visual

## Stacked Avatars

- Displayed in a flex row
- Each avatar: 40x40px, **square** (0px radius), 2px solid `border-buffer` (ivory) outline so adjacent avatars read distinctly
- Overlap: -12px negative margin on all except first

### Stacked Counter ("+3")
- Same size as avatars (40x40px), square (0px radius)
- Background: `brand` (slate-dark), text: `surface-page-base` (ivory)
- Font: Anthropic Sans 13px, weight 500
- Border: 2px solid `border-buffer` (ivory)
- Same overlap margin as other avatars

## Avatar with Text

- Layout: flex row, 12px gap between avatar and text
- Avatar: 40x40px, square (0px radius), cover fit
- Name: Anthropic Sans 15px, weight 500, `heading` color
- Subtitle / role: Anthropic Sans 14px, weight 400, `body-subtle` color
- Vertical alignment: center

## Status Indicator Dot

- 8x8px square (0px radius — never circular, even on circular avatars)
- Positioned absolute: 0 bottom, 0 right, OR -2px outside the avatar
- 1px border in `border-buffer` (ivory)
- Background per status:
  - Online: `success` (olive)
  - Away: `warning`
  - Offline: `body-muted`
  - Do not disturb: `danger` (clay-ember)

## Circular Avatar (chat / messaging only)

When a chat/conversation context demands a circular avatar:
- Radius: 9999px (full)
- All other specs identical
- Status dot remains 0px-radius square (the dot does not become circular)
- This is the only place full-radius shapes appear in the system.

## Rules

- **Default to square 0px-radius avatars** — circular only inside chat/messaging surfaces.
- **No drop shadows** under avatars.
- **No glow rings.** Bordered avatars use a solid 1–2px ink line.
- **Initials use Anthropic Sans, never the serif.** The serif at display scale is reserved exclusively for dark feature cards.
- **Status dots are square**, even when paired with circular avatars — preserves the system's formal language.
- **Cover-fit images.** Never apply `object-fit: contain` to avatars; faces should fill the frame.
