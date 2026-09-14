<!-- Заархивировано 2026-08-07. Восстановить: bash scripts/plan/restore_block.sh 06 -->

## БЛОК 06 — Каркас парсеров: утилиты, исключения, ParserService

**Статус:** [x] 2026-07-25 · **Источник:** `docs/sprints/sprint-001-backend-api.md` §2.1, §2.7 · **Ветка:** `feature/frontend-integration`

**Итог:** реализовано и проверено (40 тестов зелёные, +18 новых). Схема-цели актуализированы под Блок 02 (`(store_id, source_sku)`, `OfferPriceHistory`).

- [x] `parser/service/exceptions.py` — `ParserError`/`ParserConnectionError`/`ParserParseError`/`ParserAuthError`.
- [x] `parser/service/utils.py` — `normalize_name`, `parse_price` («4 500 ₽»→Decimal, запятая-десятичная, отбраковка нечисловых), `safe_request` (httpx + экспон. backoff, без tenacity), `compare_products` (difflib) — **16 unit-тестов** (в т.ч. retry через httpx.MockTransport).
- [x] `ParserService` — `register`/`get`/`list_parsers`/`get_statuses`/`run_one`/`run_all` (asyncio.gather, **отдельная сессия на парсер** — concurrency-safe, изоляция ошибок).
- [x] Upsert по `(store_id, source_sku)`; при изменении `price_retail` — запись в `OfferPriceHistory` + `price_changed_at` — **2 integration-теста** (создание→обновление→смена цены; run_one).
- [x] Контроллер парсера: реальная логика (`get_statuses`, `run_one` с 404/502).
- [x] Redis: `parser:status:{slug}`, `parser:lock:{slug}` (SET NX EX анти-двойной-запуск) — `RedisCache.acquire_lock/release_lock`.
- [x] `ParseResult` расширён под новую схему (`source_sku, title, price_retail, price_opt, stock_status, stock_qty, url`).
- [x] 2026-07-29 Upsert отбраковывает пустые обязательные поля, нулевые/отрицательные/нечисловые цены и продолжает прогон с остальными товарами. Устаревшие офферы деактивируются только после полного обхода без лимита/раздела/ошибок и с покрытием не ниже 80% прежнего активного каталога.
