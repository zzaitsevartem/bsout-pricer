# Gates: 1.2

OWNS: frontend/src/widgets/ProductSearch/ui/ProductSearchField.test.tsx, frontend/src/widgets/ProductSearch/ui/DeviceSearch.test.tsx, frontend/src/app/search/_components/SearchInput.test.tsx, backend/tests/integration/test_device_pages.py

- [x] G1: Terra regression cases cover all popular destinations and shared interactions
  EVIDENCE: Terra authored behavioral cases for five destinations across three hosts by click/keyboard, callback fallback and preserved device/product behavior. Parent runnable reverify passed; detailed test report sent to Luna for integration review.

- [x] G2: Popular catalog and shared search behavioral regressions pass
  CHECK: npm run test:component -- src/widgets/ProductSearch/ui/ProductSearchField.test.tsx src/widgets/ProductSearch/ui/DeviceSearch.test.tsx src/app/search/_components/SearchInput.test.tsx
  EXPECT: Test Files  3 passed
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=8e3a6ad2f35490a6533c1150d797f330c256b8764a9178695b4dda44309912ad; exit=0; EXPECT=matched; output-sha256=2ef143f742e243e6691c6fb96a142ffa15f1867fd049a659ccdd75bed00fca2d; output-bytes=899; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries
