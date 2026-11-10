# Agent task: BScout public homepage redesign

Implement the approved redesign of the **unauthenticated public homepage only** in this repository. The accepted art direction is shown in `assets/reference/homepage-approved.png`; `homepage-current.png` shows the current product page, and `tariff-glass-reference.JPG` is the direct reference for the pricing glass treatment. Read both `ASSET_GUIDE.md` and `MASCOT_MOTION_GUIDE.md` before using the packet assets or implementing mascot motion.

## Orchestration and ownership

- **Sol (`gpt-6.1-sol`, low) is the orchestrator and integrator.** Sol owns implementation, integration, scoped verification, and the final decision. Keep the task direct and budget-aware; do not start an unnecessary full reviewer chain.
- **Luna (`gpt-6-luna`, medium) must read before implementation.** Start with read-only exploration of the current guest/auth page split, relevant frontend files, current auth/search/tariff/footer behavior, tests, nested `AGENTS.md`, `DESIGN.md`, and task-relevant skills. Report exact paths/lines and open questions to Sol. After Terra writes tests, Luna must independently read every new or changed test and report coverage gaps or incorrect assumptions. Luna does not edit production code or tests.
- **Terra (`gpt-6.1-terra`, low) writes tests only.** Sol gives Terra the confirmed behavioral contract and Luna's source findings. Terra owns only new/changed test files, not production implementation. Afterward Luna reads those tests and reports to Sol; Sol resolves any gaps and owns the implementation. If the requested model is unavailable, report that fact instead of silently substituting another model.
- **Do not use Astra.** Do not add agents unless Sol finds a concrete independent task that materially helps.

## Read first

Run the repository session-start commands from the root: `bash scripts/plan/plan_status.sh`, `git log --oneline -10`, and `git status --short`. Read the latest numbered `gptaudits` entry. Read `frontend/AGENTS.md`, `DESIGN.md`, `docs/technical-specification.md`, `.agents/skills/bscout-design-system/SKILL.md`, `.agents/skills/animate/SKILL.md`, `.agents/skills/animate/RECIPES.md`, `MASCOT_MOTION_GUIDE.md`, and the relevant current source/tests. If a linked instruction file is missing, report it and follow the instructions that exist. The repository's `DESIGN.md` contains stale palette and pricing details; the current code/configuration and this user-approved white/green direction are authoritative. The root `animate.md` is a broader route-animation brief with a different role plan; do not use its Astra assignment for this task. The user explicitly selected Sol/Luna/Terra and excluded Astra.

Luna's initial source read found these likely entry points; re-open and verify them before changing anything:

- `frontend/src/app/page.tsx` selects `HomeWidget` for guests and `AuthorizedHome` for authenticated users.
- `frontend/src/widgets/homeWidget/ui/index.tsx` composes the public landing sections.
- `frontend/src/widgets/homeWidget/ui/Hero/Hero.tsx` currently has static copy/CTAs and no hero search form.
- `frontend/src/widgets/Header/ui/HeaderSearch.tsx` currently routes submitted text to `/search?q=...`.
- `frontend/src/widgets/homeWidget/ui/Prices/Prices.tsx` and `frontend/src/widgets/TariffPlans/ui/TariffPlans.tsx` use API-backed plans.
- `frontend/src/widgets/Footer/ui/Footer.tsx` is shared; its current contact/social links and destinations must be checked. The contacts page has configured email details, while some social anchors are placeholders.
- `frontend/src/app/globals.css` already contains reduced-motion and smooth-scroll rules; `frontend/tailwind.config.ts` contains current brand tokens.

## Product and route requirements

1. Redesign the public marketing page for the existing BScout spare-parts comparison service. Keep the authenticated home page, account pages, search results, payment flows, backend behavior, and other routes working as they do now.
2. On the unauthenticated homepage, make search the primary action. Add a clear hero search field and route every guest entry point that starts a search (hero, header search on this page, search chips, and primary search CTAs) to `/register`. Preserve the typed query only if the current registration flow safely supports it; otherwise go directly to `/register`. Keep authenticated search routing unchanged.
3. Use the current API-backed tariff data and existing plan features. Do not hard-code prices from either mockup. Do not add an annual billing toggle, annual prices, or payment terms; annual billing is out of scope for now. Avoid changing the shared subscription/tariff presentation on other routes; use a scoped presentation variant if needed.
4. Keep price comparison factual and visually integrated. Do not copy the giant standalone dashboard from the old design or the sample merchant prices from the approved picture as production data. Recompose it as a compact, quiet comparison preview beside/under the hero search only if current public data supports it. Otherwise explain the comparison value or show the real configured shop marks without invented offer rows. Never mark or recommend a store unless the existing product logic explicitly does so.
5. Make the footer visually substantial, as in the approved concept, but use only real current navigation, valid routes, and configured contact/social destinations. Verify each route. Omit `href="#"` placeholders and do not invent a phone, address, social account, metric, company claim, or slogan. A large footer comes from layout and spacing, not fabricated content. `Header` and `Footer` are shared components: if the marketing page needs a distinct treatment, add a scoped variant or guest-only wrapper so the authenticated page and other routes retain their current presentation.

## Visual direction

- White/ivory page, dark charcoal typography, BScout green (`#00C078` where current tokens confirm it), crisp modern geometry, generous spacing, and a futuristic abstract spray/particle backdrop.
- No arctic mountains, no continuous paint ribbons behind content, no blue wash, and no full-page liquid-glass look. Use spray assets as small edge accents with low visual weight.
- Use the pricing reference's composition: a very large centered “Тарифы” title behind three substantial glass cards, with the card row obscuring only the lower part of the title. The page stays white; glass is deliberate and materially clear (matte/translucent surface, realistic blur/reflections, readable contrast, distinct borders and grounded shadows), not milky blobs everywhere.
- Keep the product search as the hero focal point. Mirror the hero rabbit so it faces the search/headline. Repeat the same mascot on the major sections in alternating left/right positions with varied supplied poses; keep it from covering text or controls.
- Make major sections approximately one desktop viewport high. Use `min-height`, never fixed heights that clip content. Let dense sections and mobile layouts grow naturally. The footer may take a full viewport if its real content needs it.
- The screenshot is a visual reference, not a requirement to reproduce its generated or approximate text exactly. Use truthful product copy from the live site.

## Mascot tracking, turn, and blink

The rabbit must visibly turn its **head** toward the pointer and blink naturally; do not move the entire static body as a substitute.

- Build one small reusable client-side mascot interaction component. Keep the body pose fixed. Use a separate head layer/sprite or another visually clean 2.5D technique with the pivot at the neck. Pointer direction should produce a restrained, smooth head turn/gaze response (small yaw/pitch, roughly within 6–8 degrees), return to center on pointer leave, and work independently for each mascot section.
- The asset `assets/motion/mascot-direction-blink-reference.png` shows four target states (left, center, right, blink), but appears white-backed in the preview. Verify its alpha first. If a white rectangle or seam is visible, do not ship that sprite as-is; use it only as the state reference and prepare a clean matching head/eye layer from the accepted transparent mascot art.
- Blink briefly at natural, slightly varied intervals (about every 3–6 seconds); keep the eyelid close short (around 100–140 ms), then reopen. Avoid simultaneous repeated blinking across every mascot. Start pointer/blink work only for the visible/near-visible mascot and clean up timers/listeners when it leaves view.
- Track only fine mouse pointers; do not respond to touch. Decorative mascots must not intercept clicks or keyboard focus. Under `prefers-reduced-motion`, disable head travel and scroll animation (or reduce them to the gentlest useful state); do not animate unrelated spray art continuously.
- Read and apply the installed animate skill's sequence: purpose is spatial consistency/character response; use the cheapest suitable CSS/WAAPI/React mechanism already available, animate transform/opacity only, gate hover/pointer effects, and ship reduced-motion behavior with the feature. Do not add a motion dependency without proving the repository lacks a suitable primitive.

## Section scrolling and animation

- Use the animate skill for the scroll experience. Prefer native section anchors plus CSS `scroll-snap-type: y proximity` / `scroll-snap-align: start` on desktop rather than intercepting every wheel event or adding a scroll library.
- Give major sections a target of approximately `100svh` with `min-height`; content can exceed that. Provide working anchor IDs and account for the sticky header. Ensure keyboard scrolling and reduced-motion behavior.
- On narrow/touch layouts, preserve natural scrolling and turn snapping off or keep it non-locking when content is taller than the viewport. Never trap the user between sections.
- Use `scroll-behavior: smooth` only when reduced motion is not requested. Reuse existing easing/duration tokens; avoid animating layout properties. If the implementation uses any reveal effects, keep them subtle, interruptible, and non-blocking.

## Asset handoff

Use assets from `redesign/assets/`:

- `reference/homepage-approved.png`, `reference/homepage-current.png`, `reference/tariff-glass-reference.JPG`
- `brand/Logo.svg`
- `mascots/mascot-hero.png`, `mascot-presenting.png`, `mascot-calm.png`, `mascot-pointing.png`, `mascot-pointing-alt.png`
- `motion/mascot-direction-blink-reference.png`
- `icons/benefit-icons-sprite.png`
- `splashes/spray-wide.png`, `splashes/spray-corner.png`
- `shops/profi.webp`, `shops/liberty.webp`, `shops/divizion.webp`, `shops/taggsm.webp`

Verify dimensions/alpha before selecting a runtime format. Optimize/copy only the assets actually used into the normal frontend asset location; keep this brief packet intact. Use the canonical repository logo rather than drawing a replacement. Do not place the full-page reference screenshot into the live page.

## Tests and acceptance

Terra writes focused regression tests for observable behavior, at minimum:

1. Guest hero/header search and guest search CTAs lead to `/register`; authenticated search still reaches the existing search route.
2. Mascot pointer input selects/updates head direction, pointer leave returns to center, blink transitions closed→open, and listeners/timers are cleaned up. Touch and reduced-motion cases do not run pointer-driven movement.
3. Section anchors/scroll behavior expose usable targets and respect reduced motion without trapping touch/mobile scrolling.
4. Homepage tariff presentation contains only API-backed/current monthly plans and no annual toggle; shared tariff/subscription routes are unchanged.
5. Footer renders only verified working links and configured contacts, with no placeholder or invented destination.

Luna reads all Terra tests before Sol integrates them. Sol then runs the focused frontend tests plus proportional lint/type/build checks required by the current frontend rules. Do not run unrelated suites. Perform a real desktop and mobile visual check of the guest page; verify the authenticated page was not visually changed. Preserve unrelated dirty work, do not read/edit `.env`, do not commit, and report any blocked check accurately.

## Completion report

Return a short summary of changed files, actual agent/model roles used, tests/checks and browser viewports run, and remaining limitations. Be explicit if Terra or Luna could not run with the requested model; never claim that a role/model was active based only on prompt text.
