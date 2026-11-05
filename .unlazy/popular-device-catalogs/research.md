# Popular device catalogs — routing and current coverage

## Pass 1 — route and component findings

- `frontend/src/app/devices/[model_key]/page.tsx` is the dynamic page for every `model_key`; it loads `DeviceClient`, which calls `useDevice(modelKey)`. `frontend/src/models/device/service.ts` requests `GET /devices/{encoded key}`. `backend/src/modules/catalog/controller/devices.py:13–21` performs an exact `Device.model_key` lookup and returns 404 only when there is no matching database row. This is one dynamic route, not a build-time page list.
- `DeviceClient` renders the device overview/search client on a successful response (`frontend/src/app/devices/[model_key]/DeviceClient.tsx:6–37`). The device detail API does not require auth. `SearchClient` displays device identity to guests, but gates price/catalog results behind login (`frontend/src/app/search/_components/SearchClient.tsx`, auth branch around lines 133–166). Therefore route/device availability, catalog population, and guest access are distinct.
- Before this change, `FREQUENT_SEARCHES` in `frontend/src/widgets/ProductSearch/ui/ProductSearchField.tsx:10` contained only strings. Those entries became `kind: 'frequent'` and `choose` routed all of them through `onSelect`, so hosts opened `/search?q=iPhone%20N` rather than the model page. Existing model suggestions already travel through `onDeviceSelect` with a real model key.
- The shared field is used by `HeaderSearch`, `AuthorizedHero`, and `SearchInput`. I added an optional `onFrequentSelect({label, model_key})` callback and routed the curated options through it from all three hosts. Each host pushes `/devices/${encodeURIComponent(model_key)}`. The existing `onDeviceSelect`, product selection, free-text submit, dismiss/keyboard behavior, and public callback contract remain intact. If the shared component is rendered without this optional callback, a frequent row falls back to the existing text-search callback; no fake numeric device ID is constructed.

## Pass 2 — current all-device database audit

I used read-only SQL against the already-running `bscout-postgres` container (`docker exec … psql -U bscout -d bscout …`). No `.env` was read and no service or data was changed. The inventory query checked total rows, distinct and empty `model_key`s, JSON image/code lengths, release years, per-device clusters, products, and products with at least one active store offer.

| Current database measure | Result |
|---|---:|
| Device rows | 449 |
| Distinct model keys | 449 |
| Null/blank model keys | 0 |
| Devices with clusters | 436 |
| Devices with products in those clusters | 436 |
| Devices with at least one product having an active offer | 436 |
| Devices without any cluster/catalog category | 13 |
| Devices with device photos | 2 |
| Devices with release year | 2 |
| Devices with model codes | 2 |

The 13 current devices without catalog clusters are: `explay-mph-110`, `fly-sx-230`, `honor-magic-6`, `huawei-y8`, `huawei-y8s`, `lg-kg280`, `samsung-galaxy-s22-fe`, `samsung-galaxy-s26-fe`, `samsung-galaxy-s7-ultra`, `samsung-galaxy-s8-fe`, `samsung-galaxy-s8-ultra`, `tecno-pop-4`, and `tecno-pop-8`. They have resolvable device routes, but no product clusters/categories to show. This is a data-coverage finding; this change does not seed or invent their offers.

## Pass 3 — curated models and metadata/data distinction

The public detail API was queried for each curated key. Each returned the corresponding Apple device identity. Read-only database counts show these catalog rows are populated:

| Suggestion | model_key | Clusters/categories | Products | Products with active offers | Photos | Year | Model codes |
|---|---|---:|---:|---:|---:|---:|---:|
| iPhone 15 | `apple-iphone-15` | 14 | 46 | 46 | 0 | — | 0 |
| iPhone 14 | `apple-iphone-14` | 12 | 52 | 52 | 0 | — | 0 |
| iPhone 13 | `apple-iphone-13` | 14 | 56 | 55 | 0 | — | 0 |
| iPhone 12 | `apple-iphone-12` | 12 | 44 | 44 | 0 | — | 0 |
| iPhone 11 | `apple-iphone-11` | 15 | 83 | 83 | 0 | — | 0 |

All five destinations therefore resolve to device pages and have active-offer catalog products; none currently has a device photo, release year, or model-code metadata. In the complete 449-device inventory, photos, year, and model codes each cover 2 devices. Product availability does not imply photo/specification completeness.

The route contract and each curated destination can be rechecked with:

```sh
docker exec bscout-postgres psql -U bscout -d bscout -A -F '|' -c "SELECT COUNT(*), COUNT(DISTINCT model_key), COUNT(*) FILTER (WHERE model_key IS NULL OR btrim(model_key)='') FROM devices;"
curl -sS http://127.0.0.1:8000/api/devices/apple-iphone-15
```

The 449-row route conclusion is based on the database's 449 unique nonempty keys plus the generic exact-key dynamic page/API implementation, not on manually issuing 449 HTTP requests. The five curated API keys were queried directly. Device/catalog rows with no clusters are reported separately above.

## Pass 4 — source and behavior review

The curated keys are present in `backend/src/modules/catalog/service/seed.py` and independently confirmed in the current database/API, so the five explicit destinations do not rely on old seed-only evidence. The page contract is stable `model_key`; numeric IDs are needed only by existing structured device suggestions and were not fabricated for curated entries.

No code outside the assigned files was edited. Automated behavior tests are owned by Terra in leaf 1.2; this reader/implementation leaf does not claim test results. The main runtime limitation is the existing catalog itself: 13/449 devices have no cluster/category and all five featured iPhones lack showcase photos and technical metadata. The popular-catalog routing change does not address those coverage gaps.
