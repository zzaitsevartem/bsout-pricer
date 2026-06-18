# Modals

> Dependencies: `colors.md`, `radius.md`, `shadows.md`, `borders.md`, `buttons.md`, `inputs.md`, `typography.md`

Modals are one of the few transient overlays in this system that may carry a subtle drop shadow (`shadow-modal`). The dialog body remains flat and ink-bordered with a 16px panel radius.

## Core Specs

### Overlay (Backdrop)
- Fixed, covers full viewport
- Z-index: 40
- Background: `brand` (slate-dark, #141413) at 50% opacity (no chromatic tint)
- Backdrop blur: 8px (subtle, not glassy)

### Content Container
- Background: `surface-page-base` (ivory, #FAF9F5)
- Radius: 16px (panel radius — softer than buttons/cards but still architectural)
- Shadow: `shadow-modal` (the only shadow allowed on a static modal surface — it floats over the backdrop)
- Padding: 0 (header / body / footer carry their own padding)
- Border: 1px solid `border-brand` for high-emphasis modals; `border-default` for low-emphasis confirmations
- Max-width: 520px (default), 720px (form / detail variants), 960px (full-content variants)
- Margin: auto, vertically centered with 48px top/bottom safe-zone

## Anatomy

### Header
- Padding: 24px horizontal, 20px vertical
- Bottom border: 1px solid `border-default-subtle`
- Title: Anthropic Sans 20px, weight 600, `heading` color, letter-spacing -0.005em
- Optional eyebrow: Anthropic Mono 14px uppercase `body-muted`, +0.04em tracking, 4px below title
- Close button: 32x32px Ghost variant — see `buttons.md` — 16x16px X glyph in `body-subtle`, hover `heading`

### Body
- Padding: 24px horizontal, 24px vertical
- Vertical spacing between elements: 16px (24px for spacious form layouts)
- Text: Anthropic Sans 16px, weight 400, line-height 1.5, `body` color
- Headings inside body use `h4`/`h5` from `typography.md`

### Footer
- Padding: 16px horizontal, 16px vertical
- Top border: 1px solid `border-default-subtle`
- Layout: flex row, justify-end, 12px gap between buttons
- Action buttons follow `buttons.md` (typically: secondary "Cancel" + primary "Confirm")

## Variants

### Default (Informational)
Standard header + body + footer with primary / secondary action buttons. 520px max-width.

### Pop-up (Confirmation)
Centered text, prominent icon, reduced padding:
- Body: 32px padding, text centered
- Icon container: centered, 16px bottom margin, 56x56px, square (0px radius), background per intent (`success-soft` / `danger-soft` / `warning-soft`), icon color matches `fg-success-strong` / `fg-danger-strong` / `fg-warning`
- Title: Anthropic Sans 20px, weight 600, centered
- Description: Anthropic Sans 15px, `body`, centered, max-width 360px
- Footer buttons: equal-width, full-width on mobile, justified end on desktop

### Form Modal
Body contains inputs following `inputs.md`. Vertical spacing between form elements: 16px. Helper text uses 14px `body-subtle`. Submit / Cancel pattern in footer.

### Editorial / Detail Modal (dark variant — sparing use)
For pillar content moments inside a modal:
- Background: `surface-feature-dark` (#141413)
- Radius: 24px (matches dark feature card radius)
- Title in Anthropic Serif 48–61px, weight 400, ivory
- Body in Anthropic Sans 16px, `body-subtle` mapped to ivory tone
- Close button: 32x32px Ghost with ivory glyph, hover surface tint
- Footer border: 1px `border-buffer` (ivory at low opacity)

## States

- **Open / mounting:** 200ms ease-out fade for backdrop opacity (0 → 0.5) and 180ms ease-out opacity for dialog (0 → 1). Optional 8px translate-y-down → 0 on dialog. **Never use scale-in or bounce.**
- **Focus:** First focusable element receives focus on mount; focus is trapped inside the modal until close.
- **Close:** Escape key, backdrop click (configurable), or close button. 150ms ease-out fade-out.

## Rules

- **Radius: 16px on default modals; 24px on the editorial/dark variant.** Buttons and inputs inside the modal still follow their own 0px radius.
- **`shadow-modal` is the only shadow.** Never stack additional shadows on the dialog or its contents.
- **Backdrop is slate-dark at 50% — never pure black, never a chromatic tint.**
- **No backdrop gradient or noise overlay.**
- **Close button must be present and functional** (X glyph, 32x32 hit area).
- **Accessibility:** `role="dialog"`, `aria-modal="true"`, focus trap, keyboard ESC to close, return focus to trigger on close.
- **No transform-scale animations.** Open/close is opacity + small translate only.
- Dark mode automatic via token system.
