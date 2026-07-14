# Tooltips & Popovers

> Dependencies: `colors.md`, `radius.md`, `shadows.md`, `borders.md`, `typography.md`

Tooltips and popovers are floating, transient overlays — among the few surfaces where a subtle drop shadow is permitted (`shadow-overlay`). They retain the system's flat, sharp-cornered language.

## Tooltips

Tooltips deliver short helper labels — never paragraphs, never interactive content.

### Core Specs
- Padding: 8px horizontal, 6px vertical
- Font: Anthropic Sans 13px, weight 500, letter-spacing -0.002em
- Radius: 0px (default — sharp)
- Border: 1px solid (variant-specific)
- Shadow: `shadow-overlay` (the subtle floating shadow)
- Max-width: 280px
- Transition: 150ms ease-out on opacity (0 → 1)

### Dark (Default)
- Background: `brand` (slate-dark, #141413)
- Text: `surface-page-base` (ivory)
- Border: 1px solid `border-brand`

### Light
- Background: `surface-page-base` (ivory)
- Text: `heading`
- Border: 1px solid `border-brand`

## Popovers

Popovers carry richer, multi-line content — paragraphs, links, small forms, or summary metadata. They float over content, can include interactive children, and are dismissible.

### Core Specs
- Background: `surface-page-base` (ivory)
- Border: 1px solid `border-brand`
- Radius: 0px (base)
- Shadow: `shadow-overlay`
- Max-width: 360px (default), 480px (rich variant)
- Transition: 150ms ease-out on opacity

### Header / Title
- Padding: 12px horizontal, 10px vertical
- Background: `surface-elevated` (#F0EEE6)
- Bottom border: 1px solid `border-default-subtle`
- Title font: Anthropic Sans 15px, weight 600, `heading` color
- Optional eyebrow: Anthropic Mono 12px uppercase `body-muted`, +0.04em tracking, 4px above title

### Body / Content
- Standard: 12px horizontal, 10px vertical padding; Anthropic Sans 14px, weight 400, `body` color, line-height 1.4
- Rich: 16px padding; Anthropic Sans 15px, `body`, line-height 1.5; can include lists, links, small forms

### Footer (optional)
- Padding: 12px horizontal, 10px vertical
- Top border: 1px solid `border-default-subtle`
- Layout: flex row, justify-end, 8px gap
- Action buttons follow `buttons.md` — typically a Ghost "Dismiss" + Primary action

### Close Button
- Position: top-right, 8px inset
- 24x24px Ghost button with 14x14px X glyph in `body-subtle`, hover `heading`
- 0px radius

## Arrows

- Size: 8x8px square rotated 45deg
- Background: matches the popover/tooltip background variant exactly
- Border: 1px on the two visible edges, matching the popover border color
- Position: -4px offset from the popover edge toward the trigger

## Placement & Offset

- Default offset from trigger: 8px
- Maintain a 4px viewport-edge buffer on small screens (avoid clipping)
- Reposition logic: top → bottom → right → left (preferred order) when the default placement would clip

## Rules

- **0px radius mandatory** for both tooltips and popovers — no soft corners.
- **`shadow-overlay` is permitted** because these surfaces float above the page; static surfaces still carry no shadow.
- **Dark tooltips use slate-dark fill + ivory text + slate-dark border** — never a chromatic gradient.
- **Light tooltips/popovers use ivory fill + slate-dark border** — the standard ink-line frame.
- **Arrows match the parent background color** and inherit the parent's border on visible edges.
- **No transform animations on enter/exit.** Use opacity only (150ms ease-out) — no scale-in, no slide.
- **Tooltips trigger on hover and focus** with a 200ms delay; they dismiss immediately on blur/leave.
- **Popovers trigger on click and dismiss on click outside, Escape key, or close button.**
- **Accessibility:** tooltips use `role="tooltip"`, popovers use `role="dialog"` with `aria-labelledby` pointing to the title.
- **Don't nest popovers inside popovers.** If you need that hierarchy, switch to a modal.
