# Search suggestions — final evidence review

## Pass 1 — requirement reconciliation

**Frequent searches on empty focus:** The shared field now shows `Часто ищут` with iPhone 15, 14, 13, 12, and 11 when focused and empty. The rows are local query strings, not fabricated device records, and selection uses the existing search callback. The new frontend regression cases cover authenticated and logged-out focus, click and ArrowDown/Enter selection, dismissal/reopen, typing/clear transitions, and disabled suggestions. The implementation does not send an enabled empty query to either endpoint.

**Width and responsive/theme evidence:** Reviewed the recorded CUA screenshots in `gptaudits/assets/search-suggestions-2026-11-05/desktop-light.png`, `mobile-light.png`, and `mobile-dark.png`. The panel visually aligns with the field and remains inside the viewport in both light and dark mobile captures. Driver reports measured field/panel widths of 478 px at a 1280 px desktop viewport and 318 px at a 390 px mobile viewport. The dropdown stays absolutely anchored to the shared field wrapper (`left-0 right-0`, `max-w-full`, horizontal overflow hidden); option labels can wrap. Screenshots show the five expected labels and the `Часто ищут` heading.

**Model before part:** Product suggestion responses now carry additive `display_name`; the UI renders it and still submits `canonical_name`. The backend helper moves the exact structured device/brand span to the front of canonical text, retaining the remainder. Coverage includes Samsung model boundary/punctuation cases, an iPhone structured API fixture, canonical-query preservation, and a missing-cluster fallback. Device suggestions remain before product suggestions and continue using the existing model-key selection path.

## Pass 2 — expert reread

No regression is apparent in the shared selection flow: popular rows use `onSelect` (therefore the current `/search?q=...` navigation), product rows display `display_name ?? canonical_name` but submit `canonical_name`, and device rows still call `onDeviceSelect`. Existing search/device tests also cover keyboard navigation and selection. The static empty state respects `suggestionsEnabled`; API suggestions remain auth-gated by the existing `ready` condition.

The first implementation review found an unmatched-span fallback that could leave a structured product part-first. The driver changed that fallback: when structured model text is not found, `display_name` now prefixes the authoritative structured brand/model label and retains the full original canonical text; unstructured products still retain their canonical name unchanged. The updated unit fixtures cover nonmatching models and near-prefix collisions (A53/A530 and iPhone 13/130), preserving part/model text instead of truncating it. This closes the identified model-first gap. A legacy title with a nonmatching model alias can show both the authoritative structured model prefix and the original alias; the tests verify that the canonical text is retained.

## Pass 3 — defect hunt

- Source review found no issue with empty-query endpoint constraints, fake device IDs, canonical-name navigation, or component-width anchoring.
- The driver reports `check-runtime.mjs` returned `RUNTIME_VERIFIED`: the rebuilt backend is healthy, OpenAPI includes `CatalogSuggestion.display_name`, and SHA-256 values for the running service/schema match the reviewed host source. The final isolated backend run passed 19 tests (13 helper/unit and 6 API), with 31 deselected and no skips. This review did not rerun those checks.
- CUA evidence recorded in `.unlazy/search-suggestions/GATES.md` confirms the 478 px desktop and 318 px mobile field/list widths, no mobile horizontal overflow, light/dark screenshots, and ArrowDown+Enter navigation to `/search?q=iPhone%2015`. G3 is now checked. At the time of review, aggregate G1 and G9 remained pending for direct-child ledger re-verification; no user-facing behavior gap remained identified.

## Pass 4 — polish and verification summary

The driver reports: isolated frontend component tests, lint and type checking passed; the production frontend build passed in an independent copy; isolated backend API/helper tests passed 19 cases without skips. The gate log records passing G2 and G4–G8, including the three shared search/device component test files. No tests or builds were rerun for this source-only evidence review.

**Assessment:** Both requested behaviors are implemented and supported by behavioral tests and rendered UI evidence. The final structured fallback keeps model-first labels for legacy canonical strings while preserving their detail. The rebuilt local API is healthy and verified against the reviewed source, including the additive response field. No remaining user-facing behavior gap was identified in this review.
