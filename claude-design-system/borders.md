# Borders

## Width Scale

| Context | Width |
|---|---|
| Default (buttons, inputs, cards, dividers) | 1px |
| Emphasis / focus | 2px |
| Heavy hairline (decorative section dividers) | 1px solid `border-brand` (slate-dark) |

## Style

- **Solid by default** — sharp, ink-like, hairline-precise.
- Dashed borders only for special cases like file dropzones or empty-state placeholders.
- No double, dotted, ridge, or groove styles.

## Color Defaults

- **Primary structural border:** `border-brand` (slate-dark, #141413 in light / ivory in dark) — used on primary buttons, nav buttons, top-nav scrolled separator, and any line that needs to read as "ink."
- **Subtle dividers:** `border-default-subtle` or `border-light` — used between table rows, list items, and within cards.
- **Disabled / muted:** `border-default` (cloud-medium) — used on disabled controls and de-emphasized interactive elements.
- **Status borders match intent:** success → `border-success`, danger → `border-danger`, warning → `border-warning`. Never combine status borders with chromatic accent borders in the same control.

## Rules

- **Borders are the primary depth signal.** Prefer borders over shadows for component separation — shadows are essentially absent from this system.
- **The slate-dark 1px border is a signature pattern.** Primary buttons, nav buttons, and header CTAs all carry a 1px solid slate-dark border on the ivory page base. This reads as "ink line on paper."
- Components in the same family must use matching border widths.
- Never mix 1px and 2px borders within a single component (except focus/active state).
- Never use chromatic accent colors for purely decorative borders. Clay/olive/sky borders are reserved for status communication or single-section emphasis.
- Never round borders independently of the component's radius — corners follow `radius.md`.

## Usage

| Context | Width | Color |
|---|---|---|
| Inputs / selects / textareas | 1px default; 2px on focus | `border-default` default, `border-brand` on focus, `border-danger` on error |
| Primary buttons | 1px | `border-brand` |
| Nav links / ghost buttons | 1px | `border-brand` (on light), `border-buffer` (on dark) |
| Cards (release / light) | 0px (no border) — surface color does the separation | — |
| Cards (dark editorial) | 0px (no border) — surface inversion does the separation | — |
| Tables — row dividers | 1px | `border-light-subtle` |
| Tables — header bottom rule | 1px | `border-brand` |
| Section dividers (when used) | 1px | `border-default-subtle` |
| Sticky nav (scrolled state) | 1px bottom only | `border-default-subtle` or `border-default` |
| Focus ring (interactive elements) | 2px solid offset | `border-brand` (no glow, no blur) |
