# Gates: search integration

- [x] G1: Reader, test author and final reporter evidence independently reviewed; exact child leases released
  EVIDENCE: Luna research and final report reviewed; Terra tests independently reverified; all exact leaf leases released after verification. Fallback gap returned for second Terra/Luna pass and closed.

- [x] G2: Search behavior regression tests all pass
  CHECK: npm run test:component -- src/widgets/ProductSearch/ui/ProductSearchField.test.tsx
  EXPECT: Test Files  1 passed
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=d4a3447562042686cb65fbd771cb8fe4106d4c48d3e163faaa26319adb08d23f; exit=0; EXPECT=matched; output-sha256=6762994dd517fc393dc0671fd0d5090a56e438edc52c4be784398c44319c3320; output-bytes=632; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries

- [x] G3: Responsive width, themes, labeling and interaction reviewed against implementation and rendered UI
  EVIDENCE: Driver CUA review: desktop 1280 viewport input/list 478px; mobile 390 viewport input/list 318px with no horizontal overflow. Light/dark mobile screenshots and desktop-light.png saved in gptaudits/assets/search-suggestions-2026-11-05. ArrowDown+Enter navigated guest header to /search?q=iPhone%2015. Product display/selection independently covered by frontend tests and isolated backend API tests.

- [x] G4: Frontend lint succeeds
  CHECK: npm run lint
  EXPECT: No ESLint warnings or errors
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=4eb227d4b8b4d69225185980807c29d86e798d1a1e3eea20b29d9ce92d931225; exit=0; EXPECT=matched; output-sha256=6ade3a82f8ec62070c22678a5f3261656993fd94a07b6da5adc25a2385b2fce5; output-bytes=76; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries

- [x] G5: Frontend type checking succeeds
  CHECK: npx tsc --noEmit --incremental false && node -e "console.log('TYPES_VALID')"
  EXPECT: TYPES_VALID
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=b4c8ee44b59a8ecf6f681159b3d6728edf9ce9ae0000263c45d4df21fe518e68; exit=0; EXPECT=matched; output-sha256=11ca5793e605608f3853627587817dd3843790526cc963bf930f5e2212a685fb; output-bytes=12; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries

- [x] G6: Isolated backend API and helper tests pass without skips
  CHECK: node .unlazy/search-suggestions/check-backend.mjs
  EXPECT: BACKEND_SUGGESTIONS_VERIFIED
  EVIDENCE: automatic-evidence=v1; definition-sha256=a7af40777c7979c3e89e3022022fd85ab9558528a539e3a3b2fc6fc267d028d0; exit=0; EXPECT=matched; output-sha256=599fa7b49d2d5924931647f131e206e648982b9f0cc17b49a12519235b1fe744; output-bytes=671; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=3417b9840372/35 entries

- [x] G7: Production frontend build succeeds in an independent copy
  CHECK: node .unlazy/search-suggestions/check-build.mjs
  EXPECT: FRONTEND_BUILD_VERIFIED
  EVIDENCE: automatic-evidence=v1; definition-sha256=08600b0fcb1bd9419d77c056db86a26a6a3b258576d4d1dbad62238dbb503f35; exit=0; EXPECT=matched; output-sha256=b0b3ca557ef00bd4a3d65e0c216c2e9d7952bfab9aaef85fc82c94531a68fe9a; output-bytes=2501; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=3417b9840372/35 entries

- [x] G8: Existing shared search and device tests pass together
  CHECK: npm run test:component -- src/widgets/ProductSearch/ui/ProductSearchField.test.tsx src/widgets/ProductSearch/ui/DeviceSearch.test.tsx src/app/search/_components/SearchInput.test.tsx
  EXPECT: Test Files  3 passed
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=8e3a6ad2f35490a6533c1150d797f330c256b8764a9178695b4dda44309912ad; exit=0; EXPECT=matched; output-sha256=08027433d3e1548fd85379cabeb7744bc2f9cbc698fa95b2704de7936a118a29; output-bytes=897; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries

- [x] G9: All direct child ledgers are independently reverified
  CHECK: node /Users/zzaitsevartem/.codex/skills/unlazy/scripts/gate-check.mjs --root . --cwd . --reverify .unlazy/search-suggestions/gates/leaf-1.1.md .unlazy/search-suggestions/gates/leaf-1.2.md .unlazy/search-suggestions/gates/leaf-1.3.md
  EXPECT: ALL MET
  EVIDENCE: automatic-evidence=v1; definition-sha256=ffa5d9d784a9a1421bb0fbc3ea988ad9ecafd00e2cdee5565169d750f1aee183; exit=0; EXPECT=matched; output-sha256=617274aeaecd9cc4b8387ec7203c120273246d01a1eab7783dad8b402fc2cbfc; output-bytes=1220; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=3417b9840372/35 entries

- [x] G10: Local backend is healthy and runs the exact reviewed source and new response schema
  CHECK: node .unlazy/search-suggestions/check-runtime.mjs
  EXPECT: RUNTIME_VERIFIED
  EVIDENCE: automatic-evidence=v1; definition-sha256=0035ddacfba2cf6252cd51e84cb545517962a7facd548d442d054d0931fcd7de; exit=0; EXPECT=matched; output-sha256=032d3454a7629ea44544c5d4020ee44955e37cd657b58dda4837070712520d78; output-bytes=17; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=3417b9840372/35 entries
