# Popular device catalogs — final evidence

## Pass 1 — routing and shared entry points

Empty-focused search keeps the five curated labels, but clicking or keyboard-selecting them now opens their corresponding `/devices/{model_key}` catalog. `ProductSearchField` sends a typed `{label, model_key}` through optional `onFrequentSelect`; `HeaderSearch`, `AuthorizedHero`, and `SearchInput` each route to the encoded device key. If the shared field has no such callback it preserves the ordinary text-search fallback, without inventing a device ID. Existing structured-device, product, dismissal, and typed-search behavior remains in place.

The UI regression scope is all three shared hosts; curated options select model routes by both pointer and keyboard. Existing panel sizing, dismissal and typed search remain unchanged. The live database had 449 device rows, all with distinct, nonempty `model_key`s. The generic dynamic `/devices/[model_key]` page and exact-key public detail endpoint provide a route for every current row. Of those 449 devices, 436 have catalog clusters/products and at least one product with an active offer. Thirteen resolve to device pages but have no catalog clusters: `explay-mph-110`, `fly-sx-230`, `honor-magic-6`, `huawei-y8`, `huawei-y8s`, `lg-kg280`, `samsung-galaxy-s22-fe`, `samsung-galaxy-s26-fe`, `samsung-galaxy-s7-ultra`, `samsung-galaxy-s8-fe`, `samsung-galaxy-s8-ultra`, `tecno-pop-4`, `tecno-pop-8`.

## Pass 2 — populated catalog and metadata audit

All five curated destinations were read from the live API and matched the expected Apple device. Current catalog counts are:

| Suggestion | model_key | Categories/clusters | Products | Products with active offers |
|---|---|---:|---:|---:|
| iPhone 15 | `apple-iphone-15` | 14 | 46 | 46 |
| iPhone 14 | `apple-iphone-14` | 12 | 52 | 52 |
| iPhone 13 | `apple-iphone-13` | 14 | 56 | 55 |
| iPhone 12 | `apple-iphone-12` | 12 | 44 | 44 |
| iPhone 11 | `apple-iphone-11` | 15 | 83 | 83 |

Device data remains sparse: only 2/449 records have images, 2/449 have a release year, and 2/449 have model codes. None of the five popular iPhones has any of those fields. This change verified navigation and catalog availability; it did not fill photos/specs or seed empty catalogs.

## Pass 3 — regression and build evidence

- Terra’s final command `npm test -- --run src/widgets/ProductSearch/ui/ProductSearchField.test.tsx src/widgets/ProductSearch/ui/DeviceSearch.test.tsx src/app/search/_components/SearchInput.test.tsx` passed **48 tests in 3 files**. Terra reports coverage for all five destinations by click and keyboard across the three hosts, callback fallback, and preserved device/product behavior. The driver's independent gate rerun is recorded in `/private/tmp/bscout-popular-leaf-reverify.log`: the same three component files passed, exit 0, output SHA-256 `3fcefaa5d0aac87c8f35dcab15d9cb94670e99078eed4f2ee6b598f7bfbac7e6`.
- Root independently reran the shared suites, lint, TypeScript, and production build; G1, G4, G5, and G6 passed. Evidence is in `/private/tmp/bscout-popular-root-reverify.log`. Lint command: `npm run lint`. Types: `npx tsc --noEmit --incremental false && node -e "console.log('TYPES_VALID')"`. Build command: `npm --prefix /private/tmp/bscout-popular-build run build && node -e "console.log('POPULAR_BUILD_VALID')"`.
- Terra's isolated build copy is `/private/tmp/bscout-popular-build`; setup excluded `.env*`, `.next`, `node_modules`, and `*.tsbuildinfo`, then copied installed `node_modules`. Terra reports Next 14.2.35 generated 25 static pages, including dynamic `/devices/[model_key]`. Terra noted missing optional `sharp` and outdated `caniuse-lite`; root's independent build passed as well. No separate persistent Terra log path was supplied for the initial lint/types/build runs.
- Live read-only SQL used the existing Docker PostgreSQL container (`docker exec bscout-postgres psql -U bscout -d bscout ...`); the five public API checks used `curl http://127.0.0.1:8000/api/devices/{model_key}`. No `.env` was read, and no service was restarted or modified.

## Pass 4 — remaining limits and conclusion

`git diff --check` passed. Backend device-page integration tests were not rerun for this frontend routing correction. No browser screenshot/visual QA was performed for the new routing; behavior is covered by the shared UI tests and live device API reads. Existing panel layout was not changed. No routing gap remains; the 13 empty catalogs and missing iPhone photos/specs are existing data limitations, not failures of these destinations.

**Conclusion:** All requested popular suggestions resolve to the matching populated model catalogs from each shared entry point by click and keyboard. Current catalog availability and metadata coverage are measured and reported separately from route existence.
