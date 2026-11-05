# Gates: Terra actual source
OWNS: .unlazy/source-completion-review/results/**

- [x] G1: live API exposes source
  CHECK: python3 .unlazy/source-completion-review/results/check_openapi.py
  EXPECT: PASS: runtime OpenAPI exposes source
  EVIDENCE: automatic-evidence=v1; definition-sha256=274d1035884c13a154fcea5f049498058a261f0c5a018a1bb30e887da76990eb; exit=0; EXPECT=matched; output-sha256=6dfd363104121f5756fb1ad1b44563c9979de1bd0ed59dd95bf9d96b2d5e1dac; output-bytes=70; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=3417b9840372/35 entries

- [x] G2: real screenshot product source matches cheapest offer
  CHECK: docker exec -i bscout-backend python - < .unlazy/source-completion-review/results/check_real_catalog.py
  EXPECT: PASS: authenticated live catalog source matches cheapest detail offer
  EVIDENCE: automatic-evidence=v1; definition-sha256=31e35877415e08f7987c89a6e4158244f64a3b6c6835b4afe2aae91e7bb9c0d1; exit=0; EXPECT=matched; output-sha256=c18e5add55351f68df7f8005f0e9405c2baf89d800958ff8e83e78c77dbdcecf; output-bytes=1149; shell=/bin/sh; cwd=/Users/zzaitsevartem/Desktop/projects/bscout; path=3417b9840372/35 entries

- [ ] G3: real card visually confirmed
  EVIDENCE: pending

ABANDON: G3 CUA browser unavailable; external headless path prohibited by tool instructions.
