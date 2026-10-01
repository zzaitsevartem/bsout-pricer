<!-- Заархивировано 2026-08-07. Восстановить: bash scripts/plan/restore_block.sh 02 -->

## БЛОК 02 — Ядро данных: канон, offers, справочники, матчинг

**Статус:** [x] 2026-07-25 · **Ветка:** `feature/frontend-integration` (выполнено в текущей автономной сессии, не в отдельной `feature/db-core`)

**Итог:** реализовано и **проверено на живой БД**: миграция `336d8cc4267a` round-trip up→down→up без ошибок; 20 доменных таблиц + extensions `citext`/`pg_trgm` + 6 GIN-trgm/partial индексов + CHECK/uniq на месте; `uvicorn`/`/api/health` → 200; 22 теста зелёные (в т.ч. 4 новых: uniq(store_id,source_sku), CHECK stock_status, opt-цена/наличие, seed-идемпотентность). Файлы ruff-clean.

**Проблема.** Текущее ядро (`products`) — плоское: одна таблица смешивает предложение магазина и идентичность товара, связь между магазинами — только через строку `normalized_name`. Нет оптовой цены (а опт есть у всех источников: Розница/Опт, Столичный/опт), наличие — только `bool` (теряем «Мало»/«2 шт.»/«Предзаказ»), нет `uniq(store_id, external_id)` (повторный парсинг плодит дубли), нет канона, справочников, очереди модерации. Это не даёт корректно сравнивать цены и матчить товары между магазинами. Таблицы `products`/`price_history` **пусты** (проверено: 0 строк) — реструктуризацию делаем сейчас, ДО того как парсеры (Этап 3) начнут писать данные, чтобы не рефакторить ядро повторно.

**Границы и пересечения (важно — этот блок фундамент для 05/06/07):**
- **Порядок:** выполняется ДО блоков 05/06/07 и переименовывает их цели: `normalized_name`→`store_offers.normalized_title`, `PriceHistory`→`offer_price_history`, `(store_id, external_id)`→`(store_id, source_sku)`. **Не начинать 05/06/07 до закрытия 02**; после — актуализировать их формулировки под новые имена.
- **С Блоком 05 (pg_trgm):** расширение `pg_trgm` + GIN-trgm заводятся ЗДЕСЬ (таблицы новые, индексы — часть core-миграции). Блок 05 **не дублирует** `CREATE EXTENSION`/GIN — он лишь добавляет `similarity()`-логику и гейтинг по подписке, указывая на `store_offers.normalized_title`.
- **С Блоком 06 (парсеры):** схема ЗДЕСЬ (констрейнт `uniq(store_id, source_sku)`, новые колонки). Сам upsert-метод, запись истории цен и расширение `ParseResult` — в Блоке 06 (логика поверх этой схемы). Не дублировать.
- НЕ трогает Блок 01 (фронт/auth/кабинет/подписка). `users`/`subscriptions`/`stores` — не меняем; `search_history` — только `filters` JSON→JSONB.
- `categories` (публичный `/api/categories`) — **оставляем как есть**; таксономию парсинга вводим отдельной `part_types`, конвергенцию откладываем.

### Фаза 0 — Инфраструктура схемы и техдолг
- [x] `naming_convention` в `Base.metadata` (`src/database.py`).
- [x] Расширения PG в миграции (`op.execute`): `pg_trgm`, `citext`.
- [x] `search_history.filters` → `JSONB`.
- [x] `planenum` не трогали.

### Фаза 1 — Справочники (reference data)
- [x] Модели `brands, devices, device_aliases, part_types, part_type_synonyms, quality_tiers, quality_tier_synonyms, colors, color_synonyms, stopwords` (`src/modules/catalog/model/catalog.py`).
- [x] Регистрация моделей — через реестр `src/db_metadata.py` (импортируется из `env.py` и тест-conftest; DRY, устраняет дрейф).
- [x] Идемпотентный сид `catalog/service/seed.py` (10 part_types + синонимы, 5 quality_tiers + синонимы, 5 брендов, 4 устройства) — тест идемпотентности зелёный.

### Фаза 2 — Ядро (offers / канон / история / модерация)
- [x] `store_offers` (бывш. `products`): `price_opt, price_old, stock_status(CHECK), stock_qty, raw jsonb, is_active, match_status(CHECK), match_confidence, first/last_seen_at, price_changed_at, product_id(SET NULL)`; **`uniq(store_id, source_sku)`**.
- [x] Канон `products`: `cluster_id, quality_tier_id, brand_id, key_attrs jsonb, canonical_key(uniq), canonical_name`.
- [x] `clusters` (`device_id`, `part_type_id`, uniq, `offers_count/min_price_*`).
- [x] `offer_price_history` (+`price_opt`, `stock_status`, FK на offer).
- [x] `match_candidates` (offer↔product, `score`, `features` jsonb, `status(CHECK)`, `decided_by/at`).
- [x] Индексы: GIN trgm (`normalized_title`, `canonical_name`, синонимы/alias через `::text`), partial `price_retail WHERE is_active`, FK-индексы.

### Фаза 3 — Миграция Alembic
- [x] Модели переопределены, `env.py` через `db_metadata`.
- [x] Миграция `336d8cc4267a` (autogenerate + ручная дописка extensions/GIN/partial).
- [x] `upgrade head` → `downgrade -1` → `upgrade head` — чисто.

### Фаза 4 — Адаптация существующих модулей
- [x] `products` (service/schema/controller) + `admin_service` переведены на `StoreOffer`; `uvicorn` стартует, `/api/products` защищён (403 без токена).
- [-] (отложено в Блок 06) `ParseResult`, upsert по `(store_id, source_sku)`, запись истории цен.

### Проверка/DoD
- [x] `alembic upgrade head` + round-trip down/up — без ошибок.
- [x] Модели импортируются, app стартует, `/api/health` → 200.
- [x] uniq `(store_id, source_sku)`, CHECK `stock_status`, opt-цена/наличие — покрыты integration-тестами (зелёные).
- [x] Ручные проверки занесены в `MANUAL_VERIFICATION.md`.

**Известные риски/заметки:**
- autogenerate НЕ генерирует extensions/CHECK/GIN-trgm/partial — обязательны ревью и ручная дописка ревизии.
- Переименование `products`→`store_offers` ломает текущие `products`/`search` модули и цели блоков 05/06/07 — правятся в Фазе 4; данных нет (0 строк), риск низкий.
- Порт БД в среде — `5434` (`backend/.env`), в `.env.example` — 5432; миграции гонять на реальный порт.
- Конвергенция `categories`↔`part_types` намеренно отложена, чтобы не задеть публичный `/api/categories` и Блок 01.
