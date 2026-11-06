# Gates: HOT 30 model separation

OWNS: backend/src/modules/catalog/service/seed.py, backend/src/modules/catalog/service/extractor.py, backend/tests/unit/test_extractor.py, .unlazy/hot30-fix/**, gptaudits/67.md

Scope: Separate HOT 30 Play from HOT 30, preserve HOT 30i, repair affected live offers without changing catalog architecture.

- [ ] G1: Extractor regression suite distinguishes HOT 30, Play and 30i and rejects unknown Play fallback
  CHECK: docker exec -e PYTHONPATH=/app:/tmp/hot30-test-deps bscout-backend python /tmp/hot30_run_tests.py
  EXPECT: HOT30_REGRESSIONS_VERIFIED
  EVIDENCE: pending

- [ ] G2: Selected single-model Play offers are correctly linked or retained for review, and original identities and prices survive
  CHECK: docker exec -e PYTHONPATH=/app bscout-backend python /tmp/hot30_verify.py
  EXPECT: HOT30_LIVE_VERIFIED
  EVIDENCE: pending

- [x] G3: Root cause and scope of architecture changes reviewed with Luna findings
  EVIDENCE: Luna identified multi-model offer 13117 as unsafe for forced Play rematching; it was excluded and its full snapshot verified unchanged. Review offer 20873 remains unlinked and in review. The HOT30 source diff adds a suffix and a seed entry, with no broad matching architecture refactor.
