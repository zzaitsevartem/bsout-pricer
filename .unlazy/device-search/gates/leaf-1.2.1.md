# Gates: Search backend

OWNS: backend/src/modules/products/**, backend/tests/integration/test_device_search.py, backend/tests/unit/test_product_search.py

- [x] G1: Model discovery matches device aliases and keeps exact device filtering across categories and variants
  CHECK: docker exec -e PYTHONPATH=/tmp/testing:/app -e REDIS_HOST=bscout-device-search-redis bscout-device-search-check python -m pytest tests/integration/test_device_search.py tests/integration/test_comparison_api.py tests/integration/test_export.py tests/integration/test_fuzzy_search.py tests/unit/test_search_predicate.py tests/unit/test_product_search.py -q -p no:cacheprovider
  EXPECT: /80 passed[^\n]*$/m
  CWD: .
  EVIDENCE: automatic-evidence=v1; definition-sha256=43e992742fbd7f4e3319fedf1d66531b4c37fa95c77fe3b9ba64de587e547e09; exit=0; EXPECT=matched; output-sha256=aa9c22bb948bdf251b8b68acd47fb0d266f1ea910d2391c5897fe2e56637136f; output-bytes=606; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/.unlazy/device-search/gates; path=3417b9840372/35 entries

- [x] G2: Changed backend sources satisfy repository lint
  CHECK: docker exec -e PYTHONPATH=/tmp/testing:/app bscout-device-search-check python -m ruff check --no-cache src/modules/products tests/integration/test_device_search.py tests/unit/test_product_search.py
  EXPECT: All checks passed!
  CWD: .
  EVIDENCE: automatic-evidence=v1; definition-sha256=47f601cd3e449a3d69173a8e0c81d6bfe8156563ac2ae114de1f0a132373ada7; exit=0; EXPECT=matched; output-sha256=82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18; output-bytes=19; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/.unlazy/device-search/gates; path=3417b9840372/35 entries
