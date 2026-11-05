# Factual report: missing source on real catalog cards

## Actual changes and authorship

The source feature was added in the previous turn by the main agent: catalog rows rank active linked offers after the existing store, retail-price and stock filters, then select the lowest retail price with offer ID as the deterministic tie-breaker. The response includes offer/store identity and URL; the card renders a linked “Источник цены” or an explicit fallback. The Zod schema defaults an omitted source field to `null` for compatibility with older responses. Terra authored the regression tests. In this session Terra rebuilt the backend runtime and performed live checks; Luna read the source/configuration and authored this report and `gptaudits/60.md`. Main coordinated and reviewed.

## Why every real card showed “Источник недоступен”

The API container was healthy but stale. Read-only inspection showed `bscout-backend` was created on 2026-11-05, had no bind mounts, and its `CatalogItemResponse.model_fields` did not contain `source`. Its code hashes differed from the current workspace. The compose backend is built from `./backend` without source mounts; the Dockerfile copies `src` into the image, so source edits do not hot-reload into this service.

The old API response model omitted `source`; the frontend schema converted that missing key to `null` using `.nullable().default(null)`, and the card displayed its fallback. The fallback therefore hid a stale runtime rather than indicating a missing store offer. The screenshot’s one-store/one-offer detail and source image were consistent with this diagnosis.

## Correction and evidence

Terra ran `docker compose up -d --build --no-deps --force-recreate backend`. Only the API container was rebuilt/recreated; no migration, database, Redis, worker, or unrelated service was touched. The runtime OpenAPI check passed with `CatalogItemResponse: source=True`.

An authenticated, read-only request for the exact screenshot product returned retail price **7.00**, source **Профи (`profi`)**, the Siriust product URL, and one offer. The source offer ID, store ID, URL and price matched the first (cheapest, ordered by price then ID) offer in the detail response. Terra’s script queried only one active user’s numeric ID to mint a short-lived token in memory; it printed no token, secret, account identifier or other user PII. The endpoint and detail query did not write application data.

Regression evidence from Terra’s prior run, on unchanged source code: backend comparison API **38 passed**; frontend card **5/5 passed**; TypeScript, frontend lint, Ruff and Python syntax checks passed. These predate the runtime rebuild and are historical code-test evidence, not a post-rebuild test rerun.

## Remaining verification

The live API source is verified, but no rendered-page screenshot was obtained. The isolated browser was unavailable and separate Chrome-tab creation failed; headless browser use was prohibited. No claim is made that a browser-rendered card was visually verified. Visual confirmation remains a manual follow-up.

No real `.env` file was read. No commit was made. The prior user browser session was not accessed.
