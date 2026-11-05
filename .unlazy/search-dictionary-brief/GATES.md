# Gates: search dictionary task brief

OWNS: .unlazy/search-dictionary-brief/GATES.md, vocabulary-audit.md, docs/plan/MASTERPLAN.md, gptaudits/62.md

Scope: prepare a source-grounded, copy-ready task for tomorrow's search normalization work without changing product code or running tests.

- [x] G1: current backend and frontend search path is traced to source files and distinguishes existing keyboard-layout correction, ё handling, transliteration, and suggestion/catalog flows
  EVIDENCE: `vocabulary-audit.md` sections “Что уже есть” and “Контракт”; source line map also recorded in `gptaudits/62.md`.

- [x] G2: library and dictionary recommendation compares current primary sources and makes separate, bounded decisions for layout conversion, е/ё equivalence, and transliteration
  EVIDENCE: `vocabulary-audit.md` sections “Архитектурное решение” and “Библиотеки”; upstream/PyPI and PostgreSQL primary links are recorded there.

- [x] G3: acceptance matrix includes positive, mixed/ambiguous, and negative controls and preserves model, SKU, numeric, and filter semantics
  EVIDENCE: `vocabulary-audit.md` “Acceptance matrix” and “Контракт и границы реализации” include the keyboard mapping, both e/ё directions, translit/mixed queries, model/SKU negative controls, filters, sorting, and variant budget.

- [x] G4: copy-ready tomorrow task names exact ownership, roles, dependencies, files, verification expectations, risks, and unresolved decisions
  EVIDENCE: `vocabulary-audit.md` “Файлы и владение на завтра”, “Ожидаемые проверки”, and “Сложность и вопросы”.

- [x] G5: existing live plan and next numbered audit are updated consistently without overwriting unrelated work
  EVIDENCE: `docs/plan/MASTERPLAN.md` adds the 2026-11-07 task; `gptaudits/62.md` records it. Existing `gptaudits/61.md` and its Masterplan row were preserved.
