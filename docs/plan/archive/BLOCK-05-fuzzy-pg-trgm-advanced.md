<!-- Заархивировано 2026-08-07. Восстановить: bash scripts/plan/restore_block.sh 05 -->

## БЛОК 05 — Fuzzy-поиск (pg_trgm) для тарифа advanced

**Статус:** [x] 2026-07-25 · **Источник:** `docs/sprints/sprint-001-backend-api.md` §1.5 (остаток) · **Ветка:** `feature/frontend-integration`

**Итог:** реализовано и проверено (42 теста, +2 новых).

- [x] `CREATE EXTENSION pg_trgm` — заведено в Блоке 02.
- [x] GIN-trgm индекс — `ix_store_offers_normalized_title_trgm` (Блок 02).
- [x] `similarity()`-поиск в `product_service.search(fuzzy=True)`: фильтр оператором `%` (index-backed), сортировка по `similarity()` desc; fallback ILIKE для не-advanced.
- [x] Гейтинг: `subscription_guard.is_fuzzy_enabled(db, user_id)` → fuzzy только при активной подписке `advanced`; контроллер `/api/products` вычисляет `fuzzy` и передаёт в сервис.
- [x] Тесты: fuzzy находит опечатку («дислей iphone 13»), ILIKE — нет; `is_fuzzy_enabled` True только для advanced. Релевантность на больших реальных данных — в `MANUAL_VERIFICATION.md` (нужны спарсенные данные).
