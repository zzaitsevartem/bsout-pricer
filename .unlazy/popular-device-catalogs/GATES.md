# Gates: popular device catalog integration

- [x] G1: Shared entry point regression suites pass
  CHECK: npm run test:component -- src/widgets/ProductSearch/ui/ProductSearchField.test.tsx src/widgets/ProductSearch/ui/DeviceSearch.test.tsx src/app/search/_components/SearchInput.test.tsx
  EXPECT: Test Files  3 passed
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=8e3a6ad2f35490a6533c1150d797f330c256b8764a9178695b4dda44309912ad; exit=0; EXPECT=matched; output-sha256=a9475a6d9e02fb3090a790238027096fcb6e8a479d26ebbf8169123b3c156a89; output-bytes=898; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries

- [x] G2: Luna report reconciled all C1-C4 requirements and child leases released
  EVIDENCE: Luna research/report/audit61 reviewed; all five populated destinations and three hosts covered by Terra cases with independent rerun. All449 device keys mapped via generic route contract,13 empty clearly reported. Exact child leases released.

- [x] G3: All direct child evidence independently reverified
  CHECK: node /Users/zzaitsevartem/.codex/skills/unlazy/scripts/gate-check.mjs --root . --cwd . --reverify .unlazy/popular-device-catalogs/gates/leaf-1.1.md .unlazy/popular-device-catalogs/gates/leaf-1.2.md .unlazy/popular-device-catalogs/gates/leaf-1.3.md
  EXPECT: ALL MET
  EVIDENCE: automatic-evidence=v1; definition-sha256=c41c28e2763ffb82db99f33af22f3dd71cec4c482ecaac31414d1f259f35ce94; exit=0; EXPECT=matched; output-sha256=78ea5e300f69a8e99e406414bdd4bccf0d3f3e33a7cdeff64ec2e4282fe12a46; output-bytes=1222; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=3417b9840372/35 entries

- [x] G4: Frontend lint passes
  CHECK: npm run lint
  EXPECT: No ESLint warnings or errors
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=4eb227d4b8b4d69225185980807c29d86e798d1a1e3eea20b29d9ce92d931225; exit=0; EXPECT=matched; output-sha256=6ade3a82f8ec62070c22678a5f3261656993fd94a07b6da5adc25a2385b2fce5; output-bytes=76; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries

- [x] G5: Frontend types pass
  CHECK: npx tsc --noEmit --incremental false && node -e "console.log('TYPES_VALID')"
  EXPECT: TYPES_VALID
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=b4c8ee44b59a8ecf6f681159b3d6728edf9ce9ae0000263c45d4df21fe518e68; exit=0; EXPECT=matched; output-sha256=11ca5793e605608f3853627587817dd3843790526cc963bf930f5e2212a685fb; output-bytes=12; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries

- [x] G6: Production frontend build succeeds in Terra independent copy
  CHECK: npm --prefix /private/tmp/bscout-popular-build run build && node -e "console.log('POPULAR_BUILD_VALID')"
  EXPECT: POPULAR_BUILD_VALID
  EVIDENCE: automatic-evidence=v1; definition-sha256=c601dd7aa38aded5c1e1a83706334225da7caabff71aa689c8d2d2c01fe97551; exit=0; EXPECT=matched; output-sha256=429843b54e04a73c0acfe86a187ac70a09b6393ce73d218eca7a01646ba3723c; output-bytes=2542; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=3417b9840372/35 entries
