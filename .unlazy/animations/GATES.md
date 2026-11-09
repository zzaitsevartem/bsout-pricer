# Gates: BScout animations

OWNS: frontend/src/**, frontend/tailwind.config.ts, .unlazy/animations/**, gptaudits/69.md, gptaudits/assets/animations-2026-11-09/**, docs/plan/MASTERPLAN.md

Scope: Implement the accepted animation recommendations across actual BScout routes with accessible page transitions, reduced-motion support, verified loading/error behavior, and checked frontend quality.

- [x] G1: frontend Vitest suite passes with animation regressions covered
  CHECK: npm test
  EXPECT: Test Files
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=41457324f981b9b04c05e2e1169a10543cb36bb332f8ac3ad5519d766b1e09c5; exit=0; EXPECT=matched; output-sha256=ab37545d233fcac85244af661b67403095c55f28249a47771aeff616dd1ed8a9; output-bytes=10122; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=a74cac9ec105/35 entries

- [x] G2: frontend lint passes
  CHECK: npm run lint
  EXPECT: ✔
  CWD: frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=f579ccee8edc79af24a5c0ff16a9c308476343b1344ab7a3cc02702d7ffadf26; exit=0; EXPECT=matched; output-sha256=6ade3a82f8ec62070c22678a5f3261656993fd94a07b6da5adc25a2385b2fce5; output-bytes=76; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=a74cac9ec105/35 entries

- [x] G3: frontend production build succeeds
  CHECK: node .unlazy/animations/build.mjs
  EXPECT: Route (app)
  CWD: .
  EVIDENCE: automatic-evidence=v1; definition-sha256=bf293cf4b5996fc9857138bb07ec4bfae0580d038d897df5dec734893b389e70; exit=0; EXPECT=matched; output-sha256=1f1ed52393ca847cecc846b70a5fadcaba9729fdad8019fec5c8f3579c251b65; output-bytes=3267; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=a74cac9ec105/35 entries

- [x] G4: route transitions and motion behaviors pass browser review for reduced motion, keyboard/focus, quick navigation interruption, and small-screen layout
  EVIDENCE: Root verified in IAB at 390×844: mobile menu opened/closed in 220/160ms, Enter toggled it repeatedly without horizontal overflow, body overflow was restored after closing; rapid SPA FAQ → Contacts → Privacy and Back/Forward matched each route heading and kept content at one layer; tooltip appears on keyboard focus with opacity 1 and no transform; carousel pause/focus produced animation:none and transform:none, hid duplicate links, and all 4 original links were in bounds during Tab navigation; browser reduced-motion emulation hid the pause button while keeping four partner links exposed. The `PageTransition` reduced-motion bypass is additionally covered by its unit test. Final compiled CSS regression: carousel top825 outside720px viewport had paused/false, visible top105 running/true, then offscreen top-1335 paused/false; stronger default selector prevents Tailwind shorthand resetting pause. Automated DOM observation timed out; native browser console was not used to bypass its self-XSS warning.

- [x] G5: controlled loading checks record down-backend, delayed success, and delayed error behavior without stopping or modifying unidentified/shared processes
  EVIDENCE: On a dedicated Next instance behind a loopback QA proxy: delayed catalog detail returned 200 after 8003ms, showing product skeleton before data; simulated backend-down returned 502 in 8ms and React Query retried at about +1s/+3s/+7s before an inline error with Retry; delayed-error returned 503 on four requests at about 5s each (three retries) before inline `Fixture error` and Retry. Only the isolated test instance/proxy was used. Existing user listeners localhost:3000 PID 3665 and localhost:8000 Docker PID 1222 were not changed or stopped. An unrelated price-history request logged 904292ms wall time; cause was not established and is recorded in the audit.

- [x] G6: final motion audit confirms no unnecessary frequent-action motion, broad transition-all additions, or unmanaged continuous animation, and checks all new motion for reduced-motion behavior
  EVIDENCE: Final read-only review of the scoped frontend diff found no newly added `transition-all`/`transition: all`, no motion on query input/filter/result prices/tables, and no added animation dependency. The 160ms page opacity transition bypasses reduced-motion and cancels on path/preference/visibility/unmount; menu/tooltip transitions have reduced-motion rules; carousel auto-motion runs only while visible, pauses on hover/focus/button/tab-hidden, presents a static single-copy layout for focus/pause/reduced motion, and removes duplicate links from focus/accessibility order. Existing unrelated legacy transition-all rules were not changed. Error and global-error surfaces remain immediate.

- [x] G7: the completed implementation is documented, committed on bscout/animations, and pushed to its remote
  CHECK: node .unlazy/animations/check-push.mjs
  EXPECT: REMOTE_COMMIT_VERIFIED
  CWD: .
  EVIDENCE: automatic-evidence=v1; definition-sha256=a451f18fc5e2fd7cdb4f8be77c8897c2474d37b3b5604afcc910127d1cee579a; exit=0; EXPECT=matched; output-sha256=6a86c130c9f0033ba03f8771fff7f3f2cb884fcd00cc280a41fd987a6ecb131f; output-bytes=64; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=a74cac9ec105/35 entries
