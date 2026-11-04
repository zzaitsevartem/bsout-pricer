# Gates: Device search UI

OWNS: frontend/src/app/search/**, frontend/src/models/catalog/**, frontend/src/widgets/ProductSearch/**, frontend/src/widgets/Header/**, frontend/src/widgets/authorizedHome/**, frontend/src/models/product/**

- [x] G1: Model selection and query changes preserve coherent URL state and contextual facets
  CHECK: npm test -- src/app/search src/widgets/ProductSearch
  EXPECT: /Test Files\s+\d+ passed/
  CWD: ../../../frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=83459e0d11e2e063288d63cad987dfc08accffeccda3a1b19b080f651dea428d; exit=0; EXPECT=matched; output-sha256=33f66ffe2faab505c781623e3e5f70739f840a1c7ef21630889f308fe3f69cd1; output-bytes=1261; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries

- [x] G2: Search interface compiles with the catalog contracts
  CHECK: npx tsc --noEmit
  EXPECT: /^$/
  CWD: ../../../frontend
  EVIDENCE: automatic-evidence=v1; definition-sha256=1485d666c2404a4986a29655f91b54b8efd105453004566dbc4af8f23801ee2d; exit=0; EXPECT=matched; output-sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855; output-bytes=0; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout/frontend; path=3417b9840372/35 entries
