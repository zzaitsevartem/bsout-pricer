# Luna research evidence
Research delegated to /root/luna_research, gpt-6-luna through bscout_reader. Parent has not independently read project source.

Complexity: high, now bounded by existing Device/DeviceAlias, Cluster.device_id and Cluster.part_type_id, URL ids and shared search/export filtering. No category taxonomy migration indicated. New device suggestions + explicit model lock + contextual category facets + query reset required. Free text remains broad.

Luna observed Liberty in a separate hidden tab:
- https://liberti.ru/search/?q=iphone+13 : 546 results, Apple display and battery category counts; compatibility spans variants.
- https://liberti.ru/search/?q=iphone+13+pro : 318, includes Pro Max.
- Russian айфон 13: 833 broad results including unrelated device families; do not replicate poor precision.
- https://liberti.ru/models/apple-iphone-13/ : heading Запчасти и аксессуары для Apple iPhone 13; all 182, displays 13, batteries 7; model selection separate from free text.
- /catalog_models/phone/apple/ separates base/Pro/Pro Max.
Observed UX, no access to Liberty internal implementation.

Current code (Luna report): search_predicate matches canonical_name tokens, fuzzy aliases; numeric token boundaries do not distinguish Pro variant. ComparisonService exact device_id/part_type_id supported. Facets span whole q result but only q, no selected ids/offer filters/counts. Offer constraints apply to same StoreOffer before aggregate; preserve. Exports use same search_catalog. Device seed has iphone 13/айфон 13/ip13/iph 13 aliases. ProductSearchField suggests canonical products only, auth gated, debounce 200ms. SearchInput commits query after 350ms. SearchClient query edits currently preserve stale device_id. Existing facets response arrays id,label. Frontend :3000 existing Next PID 52689; backend :8000 docker PID 60067. Do not start competing servers. Latest numbered audit 51. Source excerpts and exact commands pending from reader.

Category decision: retain PartType dictionary and exact part_type_id filtering, extend facet scope/counts instead of rebuilding taxonomy. Device selection clears text query and resets part type; typing a new query clears old device/category. URL remains source of truth; model labels come from resolved facet data. Device suggestions should be shared by header/hero/search fields where feasible.
