# Gates: query expansion

OWNS: backend/src/modules/products/service/search_predicate.py, backend/src/modules/catalog/service/normalizer.py

- [x] G1: bounded query expansion implements the accepted positive and negative token contract
  EVIDENCE: Parent reviewed independent Luna source findings (search_predicate.py:35-45,63-95,98-120) and Terra unit/integration PASS; original first, N+min(11N,64) candidates, query regex escaping, token-level OR / word AND, explicit recognized-model/SKU safety exception revision 2. Final root rerun still required.
- [x] G2: production diff preserves interfaces, aliases, filters, ordering, storage and subscription policy
  EVIDENCE: Independent Luna source review found no blocking defect; product_service.py:50-89 and comparison_service.py:213-249,335-351,422-432,470-480 retain filters/orders; Advanced alias/typo branches search_predicate.py:74-90,117-118 retained. Only common predicate source changed; no UI/schema/storage/dependency change.
