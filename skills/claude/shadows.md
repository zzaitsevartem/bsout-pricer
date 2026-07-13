# Shadows

> **Zero box-shadows is the default policy.** Surface depth is achieved entirely through background color contrast — ivory (#FAF9F5) vs slate-dark (#141413) vs warm-card (#E3DACC) — with hard-edged transitions and no blurring. This flat-but-high-contrast approach reads as print design transferred to screen: depth through ink density, not light simulation.

| Token | CSS value | Purpose |
|---|---|---|
| shadow-none | `none` | Default for all components — buttons, cards, inputs, panels, sections |
| shadow-hairline | `inset 0 -1px 0 0 var(--border-default-subtle)` | Optional: 1px inset hairline divider for sticky nav scrolled state. NOT a drop shadow. |
| shadow-overlay | `0 4px 12px rgb(20 20 19 / 0.08)` | **Reserved exclusively** for transient floating overlays (popovers, dropdown menus, tooltip cards, modal backdrops fading in). Never on static surfaces. |
| shadow-modal | `0 8px 24px rgb(20 20 19 / 0.12)` | Reserved exclusively for modal dialog containers when they need lift over a backdrop. |

## Component Mapping

| Component type | Token |
|---|---|
| Buttons (all variants) | shadow-none |
| Cards (light release cards) | shadow-none — surface contrast vs page base is the only differentiator |
| Cards (dark editorial feature cards) | shadow-none — sit flush in their grid with no lift |
| Inputs / textareas / selects | shadow-none — borders carry separation |
| Badges / tags / metadata labels | shadow-none |
| Sticky top navigation (default) | shadow-none |
| Sticky top navigation (scrolled state) | shadow-hairline (1px inset bottom border, not a drop shadow) |
| Popovers / floating dropdowns / tooltip surfaces | shadow-overlay |
| Modal containers | shadow-modal |

## Rules

- **No shadows on cards.** Card surfaces are differentiated from the page base solely by background color contrast. The same applies to panels, sections, hero blocks, and any large UI surface.
- **No shadows on buttons.** Borders and solid fills do all the depth work.
- **No shadows on inputs.** Border thickness on focus (1px → 2px or border color shift) signals state.
- **No drop shadows under headlines, images, or icons.** The aesthetic is flat, editorial, ink-on-paper.
- **No glow halos.** Focus rings use border color shifts or a 2px solid focus ring in `border-brand` — never a soft glow.
- **No layered or stacked shadows.** Never combine shadow tokens.
- **Drop shadows are permitted only on floating, transient overlays** (popovers, modals) — and even there, the shadow must be subtle, neutral-toned, and never blurry-blue or chromatic.
- **Never use shadow as the primary separator** between two adjacent layout regions — use surface color alternation or 1px borders instead.
- **No inner shadows for "depressed" or "skeumorphic" effects** — surfaces are flat.
