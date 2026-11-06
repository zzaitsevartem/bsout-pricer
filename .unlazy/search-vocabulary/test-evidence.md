# Search vocabulary: test and runtime evidence

## Prepatch EXPLAIN (2026-11-06)

Isolated PostgreSQL 16 Alpine, temporary in-memory database, `pg_trgm` GIN on text; 100,000 synthetic titles, `ANALYZE`, about 250 matching titles per long query. `EXPLAIN (ANALYZE, BUFFERS)` recorded before production patch. These are single synthetic measurements, not a production benchmark.

| Query | Plan | Total estimated cost | Actual rows | Execution ms |
| --- | --- | ---: | ---: | ---: |
| `~* 'съ[её]мный'` | Bitmap Index Scan | 145.06 | 250 | 0.309 |
| `ILIKE '%съемный%' OR ILIKE '%съёмный%'` | BitmapOr | 210.18 | 250 | 0.247 |
| `~* '[её]мкость'` | Bitmap Index Scan | 119.18 | 249 | 0.255 |
| `ILIKE '%емкость%' OR ILIKE '%ёмкость%'` | BitmapOr | 210.18 | 249 | 0.245 |
| `~* 'пл[её]нка'` | Bitmap Index Scan | 132.12 | 247 | 0.235 |
| `ILIKE '%пленка%' OR ILIKE '%плёнка%'` | BitmapOr | 184.30 | 247 | 0.234 |
| `ILIKE '%съемный%'` | Bitmap Index Scan | 106.24 | 0 | 0.026 |
| `~* '[её]'` / `~* 'н[её]'` | Seq Scan | 2635.99 / 2386.04 | 100000 / 0 | 27.511 / 19.671 |
| bounded ILIKE OR for `е/ё` / `не/нё` | Seq Scan | 2885.99 / 2636.06 | 100000 / 0 | 51.081 / 69.755 |

Query-side regex accepted for long forms; short inputs can require sequential scans, as did measured fallback. No column function, index change, migration or backfill. 12 candidates/token and 64 query expansions tested; original candidate retained for every token.

## Automated tests

Existing `/private/tmp/bscout-history-venv`, Python 3.11.16; no dependency installation. Pytest runs from `/private/tmp` with explicit test configuration, isolated PostgreSQL and Redis on localhost random ports; no real `.env` read. Unit: 83 passed, 0 skipped. Integration: 20 passed, 0 skipped. Ruff passed for changed tests and production predicate. Passlib Python `crypt` deprecation warning only.

18 PostgreSQL positive/negative query pairs execute in both exact and fuzzy modes: layout multiword AND; both е/ё directions; three confirmed transliterations and mixed words; iPhone 15/14, SE/XR/Pro, Galaxy A52/A53, SM-A525, GT and shared-digit SKU. API tests exercise Basic versus Advanced typo behavior and deterministic layout, catalog/offers/facets/product and device suggestions, price sorting/pagination, empty state, independent store/price/stock/device/part/quality negative filters, and offers category positive/negative. Legacy substring `pro` matched `processor` and `gt` matched `bright`; protected model boundaries intentionally remove these matches. Existing offer fuzzy similarity sort remains raw-query, price ordering is tested on Basic and catalog. Tests cannot prove all real-world transliterations or all model/SKU forms.

## Runtime and browser

Canonical `docker compose up -d --build --no-deps --force-recreate backend` stalled on `docker/dockerfile:1` registry resolution and was interrupted before recreate. Offline fallback built from existing local image `b767197996513bdb1b74bcce8416e15ea71854cb00e92fbde5cef231b8f28ede` (preserved as `bscout-backend:vocabulary-rollback`), replacing `/app/src` only with current sources, no dependencies/network; image `5fd98cae0c68f714c156668fa3abb84aecf561400d4d5f9c84ce86e3e1083d8a`. Only backend recreated, no DB/Redis/worker/beat restarts or migration. Healthy; checkout and container predicate SHA256 both `db1dc217d35e4494c56576d2995e26dc978ed15309f57ceb47a2351f415535c3`. Health and OpenAPI pass. Authenticated real-data GET catalog: `защитная плёнка apple iphone 15` 8 results; `защитная plenka apple iphone 15` 8 results, all original IDs retained; expanded suggestions 6. No working DB writes.

Isolated IAB guest session on localhost displayed the original `plenka iPhone 15` unchanged in search input. It lacked an authenticated session; suggestions and authenticated UI remain unverified. Frontend uses localStorage tokens; CUA's supported evaluate is read-only and no user credentials/session were provided, so no injection into browser or existing user tab was attempted. Follow-up: sign in to an isolated session and verify suggestions and URL preserve the original query against the rebuilt backend.
