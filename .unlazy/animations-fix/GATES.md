# Gates: animation correction
OWNS: frontend/src/**, gptaudits/70.md, docs/plan/MASTERPLAN.md
Scope: restore uninterrupted CSS carousel and make route entrances clearly visible without losing content state.

- [x] G1: Route transition preserves state, focus and cancellation; duplicate links remain inaccessible
  CHECK: npx vitest run src/shared/ui/PageTransition.test.tsx src/widgets/homeWidget/ui/Carousel/Carousel.test.tsx
  CWD: frontend
  EXPECT: Test Files  2 passed
  EVIDENCE: automatic-evidence=v1; definition-sha256=3d4d0375300f4ecc12eddf3b90d30f24506ceead8015266328b59490e8a7235f; exit=0; EXPECT=matched; output-sha256=88613cc6256fbeb56716fe49e6524df49899e0d4e10471454f962b4d4555822c; output-bytes=561; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=a74cac9ec105/35 entries

- [x] G2: Frontend lint accepts the corrected components
  CHECK: npm run lint
  CWD: frontend
  EXPECT: No ESLint warnings or errors
  EVIDENCE: automatic-evidence=v1; definition-sha256=4eb227d4b8b4d69225185980807c29d86e798d1a1e3eea20b29d9ce92d931225; exit=0; EXPECT=matched; output-sha256=6ade3a82f8ec62070c22678a5f3261656993fd94a07b6da5adc25a2385b2fce5; output-bytes=76; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=a74cac9ec105/35 entries

- [x] G3: Browser confirms continuous carousel and SPA fade; reduced motion fallback is covered by tests and CSS inspection
  EVIDENCE: Real browser localhost:3000, SPA /contacts to /faq: 65 separate DOM samples opacity 1 then 0, .373145, .637579, .812231, .906284, .95264 to 1. Carousel no pause button, animation 20s linear infinite scroll, running; transform -293.327 to -826.02 between probes; keyboard focus on Profi remains running. Reduced fallback covered by unit/CSS, not emulated in browser. Screenshot /private/tmp/bscout-carousel-correction.png.

- [x] G4: Isolated production build compiles the corrected server carousel and route transition
  CHECK: node .unlazy/animations/build.mjs
  EXPECT: Generating static pages (25/25)
  EVIDENCE: automatic-evidence=v1; definition-sha256=78879d3b6c2db6a8823c93f99270f76f9920ba27123c645ab35832a05ee360de; exit=0; EXPECT=matched; output-sha256=211fbf271ec93a1fa090bfddbe10a4469b7c8fa5cd97024ce3a37a8d4fb1cdb7; output-bytes=3267; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=a74cac9ec105/35 entries
