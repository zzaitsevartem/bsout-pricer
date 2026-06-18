# Typography

> Dependencies: `colors.md`

## Core Rules

- **Primary font (UI / sans):** `'Anthropic Sans', 'Styrene B', 'Inter', 'DM Sans', system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` — all UI chrome: navigation, buttons, labels, badges, footer, body copy, light-surface headlines.
- **Display font (serif):** `'Anthropic Serif', 'Tiempos Headline', 'Playfair Display', 'Lora', Georgia, "Times New Roman", serif` — feature card headlines, editorial hero text, project titles. **Reserved for dark surfaces only** (slate-dark cards). Never use the serif at display scale on the ivory page base.
- **Mono font:** `'Anthropic Mono', 'JetBrains Mono', 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace` — technical labels, metadata field labels (DATE, CATEGORY), structured data signals. Used sparingly.
- **Fonts configured at app level — never override per-component.**
- **Headings:** weight varies by level (see scale below), `heading` text color, never `clay` or accent color.
- **Body copy:** `body` text color, never use accent color for paragraphs longer than one sentence.
- **Semantic HTML:** Use `h1`–`h6` in order, never skip levels.

## Heading Scale

### Desktop

| Element | Size | Weight | Line-height | Letter-spacing | Margin-bottom | Font |
|---|---|---|---|---|---|---|
| `h1` (display, dark surfaces) | 91px | 400 (regular) | 1.1 | normal | 32px | Anthropic Serif |
| `h1` (light surfaces) | 61px | 700 (bold) | 1.1 | -0.02em (-1.22px) | 24px | Anthropic Sans |
| `h2` | 40px | 600 (semibold) | 1.15 | -0.01em | 24px | Anthropic Sans |
| `h3` | 24px | 600 (semibold) | 1.3 | -0.005em (-0.12px) | 16px | Anthropic Sans |
| `h4` | 20px | 600 (semibold) | 1.4 | normal | 12px | Anthropic Sans |
| `h5` | 18px | 600 (semibold) | 1.4 | normal | 8px | Anthropic Sans |
| `h6` | 16px | 600 (semibold) | 1.5 | normal | 8px | Anthropic Sans |

### Responsive

| Element | Tablet (≥768px) | Mobile (default) |
|---|---|---|
| `h1` (display) | 64px | 48px |
| `h1` (light) | 44px | 36px |
| `h2` | 32px | 28px |
| `h3` | 22px | 20px |
| `h4` | 18px | 18px |
| `h5` | 16px | 16px |
| `h6` | 16px | 16px |

Mobile-first: start with mobile sizes, scale up at tablet and desktop breakpoints.

Never reduce line-height below 1.05 for any heading.

## Paragraphs

### Leading Paragraph (subheading)
- Size: 18px
- Weight: 400 (regular)
- Color: body
- Line-height: 1.4
- Letter-spacing: -0.002em
- Max width: ~64 characters
- Font: Anthropic Sans

### Normal Paragraph (body)
- Size: 16px
- Weight: 400 (regular)
- Color: body
- Line-height: 1.5
- Letter-spacing: normal
- Max width: ~70 characters
- Font: Anthropic Sans

### Small Supporting Copy (body-sm)
- Size: 15px
- Weight: 400 (regular)
- Color: body-subtle
- Line-height: 1.4
- Letter-spacing: -0.002em (-0.03px)
- Use only for helper text, captions, footer secondary content, metadata values.

### Caption
- Size: 12px
- Weight: 400 (regular)
- Color: body-muted
- Line-height: 1.3
- Use for legal text, fine print, hint text.

## UI Labels

| Context | Size | Weight | Font |
|---|---|---|---|
| Button labels | 15px | 500 (medium) | Anthropic Sans |
| Nav links | 15px | 400 (regular) | Anthropic Sans |
| Wordmark / logo lockup | 16px | 700 (bold) | Anthropic Sans |
| Input labels | 14px or 15px | 500 (medium) | Anthropic Sans |
| Captions / meta values | 14px or 15px | 400 (regular) | Anthropic Sans |
| Metadata field labels (DATE, CATEGORY) | 16px | 400 (regular), uppercase, tracking +0.04em | Anthropic Mono |

Do not apply paragraph line-height (1.5) to control labels — keep labels at 1.0–1.4.

## Type Scale Tokens

| Role | Size | Line-height | Letter-spacing |
|---|---|---|---|
| caption | 12px | 1.3 | normal |
| body-sm | 15px | 1.4 | -0.002em |
| body | 16px | 1.5 | normal |
| subheading | 18px | 1.4 | -0.002em |
| heading-sm | 20px | 1.4 | normal |
| heading | 24px | 1.3 | -0.005em |
| heading-lg | 61px | 1.1 | -0.02em |
| display | 91px | 1.1 | normal |

## Links

- **Inline body links:** Same size as surrounding text, `fg-brand` color (slate-dark, the same as surrounding ink), `text-decoration: underline`, hover → underline thickens or shifts to `fg-clay-strong` color only when the link sits in body copy. Never colorize links inside headlines.
- **CTA / arrow links:** `fg-brand` color, weight 400, no underline at rest. Append a literal arrow glyph `→` directly to the text (e.g. `Read announcement →`). On hover, an underline appears. Used for "Read announcement →", "Read the story", "Model details".
- **Display headline emphasis links (the signature pattern):** Selected keywords inside large headlines (61px+) carry a thick `text-decoration: underline` with no color change and no weight change. The underline IS the emphasis — it replaces the conventional bold/color treatment. Use only on display and heading-lg scales.

## Emphasis

- **Underline as primary emphasis device.** In display headlines, mark key nouns with a thick underline only — never bold, never color, never highlight backgrounds.
- `<strong>` for high-priority emphasis in body text only — uses weight 600, same color as surrounding text.
- `<em>` for tone emphasis only, not visual hierarchy — italic, same color.
- All-caps only for short labels and metadata: uppercase, +0.04em letter-spacing, 12–16px, Anthropic Mono for data labels (DATE, CATEGORY) or Anthropic Sans 12px weight 500 for badge text.
- Never replace the underline emphasis mechanic with color emphasis on headlines.

## Surface-Aware Typography

Type behavior changes by surface:

| Surface | Headline font | Headline color | Body color |
|---|---|---|---|
| Page base (ivory) | Anthropic Sans | heading (#141413) | body |
| Light card (elevated / warm) | Anthropic Sans | heading (#141413) | body |
| Dark editorial card (slate-dark) | **Anthropic Serif at display scale (91px)** | white (#FAF9F5) | body-subtle on dark |

**Critical:** Anthropic Serif at display scale only appears on dark surfaces. Anthropic Sans handles all light-surface headlines.

## Dark Mode

Hierarchy stays identical. Only color tokens change (automatic via CSS custom properties). Size, weight, and spacing remain constant. The serif/sans surface assignment is preserved: serif still belongs to inverted dark surfaces.
