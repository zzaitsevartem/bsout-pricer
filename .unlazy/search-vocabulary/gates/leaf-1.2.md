# Gates: tests and runtime

OWNS: backend/tests/unit/test_search_predicate.py, backend/tests/unit/test_normalizer.py, backend/tests/integration/test_search_vocabulary.py, .unlazy/search-vocabulary/test-evidence.md, .unlazy/search-vocabulary/checks/**

- [x] G1: unit regression matrix and bounded SQL pass
  CHECK: /private/tmp/bscout-history-venv/bin/python .unlazy/search-vocabulary/checks/run_tests.py unit
  EXPECT: UNIT_VOCABULARY_PASS
  EVIDENCE: automatic-evidence=v1; definition-sha256=b38c45a6aebb333fdefdc0a1532d2508660d0fef8ce1d3e6f62526c1c8c08eee; exit=0; EXPECT=matched; output-sha256=01b013fef935a89fd07b162ad99fa577fd5d9096b44da7e3b80165492eb1dcb4; output-bytes=657; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=8b4acad4ec8c/35 entries
- [x] G2: prepatch representative EXPLAIN establishes query-side policy
  EVIDENCE: prepatch EXPLAIN and bounded fallback measurements in .unlazy/search-vocabulary/test-evidence.md
- [x] G3: rebuilt backend healthy and authenticated real-data read-only API confirms expanded search
  EVIDENCE: healthy offline-derived image, matching source SHA, real authenticated read-only API in .unlazy/search-vocabulary/test-evidence.md
- [ ] G4: isolated browser verifies original query and compatible suggestions
  EVIDENCE: pending
- [x] G5: isolated PostgreSQL and Redis integration matrix passes without skips
  CHECK: /private/tmp/bscout-history-venv/bin/python .unlazy/search-vocabulary/checks/run_tests.py integration
  EXPECT: INTEGRATION_VOCABULARY_PASS
  EVIDENCE: automatic-evidence=v1; definition-sha256=de1fb9afc761b8687a68d1f4f1f12dc152cbfdafb2ac6744f82f1c71739e93f1; exit=0; EXPECT=matched; output-sha256=d066addad8a9d70f7d879fe36882c1318238c9b470ed8ea5fc9e4999f87d5931; output-bytes=584; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=8b4acad4ec8c/35 entries
- [x] G6: changed Python tests pass Ruff
  CHECK: /private/tmp/bscout-history-venv/bin/ruff check --no-cache backend/src/modules/products/service/search_predicate.py backend/tests/unit/test_search_predicate.py backend/tests/unit/test_normalizer.py backend/tests/integration/test_search_vocabulary.py
  EXPECT: All checks passed!
  EVIDENCE: automatic-evidence=v1; definition-sha256=ec326f3896d5e557d62908afb071194bd41b01d7837f04431599cec3e7404714; exit=0; EXPECT=matched; output-sha256=82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18; output-bytes=19; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=8b4acad4ec8c/35 entries

ABANDON: G4 isolated guest session lacks credentials; authenticated suggestions need a signed-in isolated browser follow-up
