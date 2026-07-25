# BScout — MASTERPLAN

> **Единственный источник задач и прогресса проекта.** Не создавайте параллельных
> `PLAN_*.md` / `TODO_*.md` — весь трекинг живёт здесь.
> Полная карта всех блоков (включая архивные) — [INDEX.md](./INDEX.md).
> Что автотестами не подтвердить — [MANUAL_VERIFICATION.md](./MANUAL_VERIFICATION.md).
> Старшинство планов и краткий протокол — в корневом `CLAUDE.md`.

## Текущий статус (сводка)

| Поле | Значение |
|------|----------|
| Активный блок | 01 — Интеграция фронтенда с бэкендом (auth, кабинет, подписка) |
| Режим | разработка · ветка `feature/frontend-integration` |
| Фаза дорожной карты | Блок 01: Фазы 1–4 реализованы + отревьюированы; **остался DoD — `npm run build && npm run lint`** (заблокирован: нет `node_modules`) |
| Обновлено | 2026-07-25 |

## Легенда статусов

`[ ]` не начато · `[~]` в процессе · `[x]` выполнено · `[!]` заблокировано · `[-]` отменено

## Протокол агента

**Холодный старт (каждая сессия):**
1. Прочитать сводку статуса выше — или `bash scripts/plan/plan_status.sh` — плюс `git log --oneline -10` и `git status`.
2. Найти первый незакрытый `[ ]`; это следующий шаг. Доложить пользователю активный блок и шаг.
3. **Не** перечитывать план целиком: детали закрытых блоков лежат в `docs/plan/archive/` и поднимаются по требованию (`restore_block.sh`).

**Во время работы:**
4. Один агент = один блок. Крупные рискованные проходы — отдельной сессией, не параллельно.
5. Параллельные агенты работают в изолированных worktree `.claude/worktrees/<block-slug>`, чтобы правки не перемешивались.
6. Что нельзя подтвердить автотестом (у проекта тестов нет) — заносить в `MANUAL_VERIFICATION.md` со статусом ⬜.
7. Правьте только свой блок и его строку в `INDEX.md` — так план не становится точкой гонки между агентами.

**Закрытие (обязательно перед концом сессии):**
8. Выполненный пункт: `[ ]` → `[x] YYYY-MM-DD`. Обновить «Текущий статус» и «Историю обновлений».
9. Блок закрыт целиком → `bash scripts/plan/archive_block.sh NN` (уносит секцию в `archive/`, флипает строку в `INDEX.md`).
10. Отдельный коммит на блок: `docs(plan): mark NN done — <результат>` (коммитить только по явной просьбе — см. `CLAUDE.md`).

---

<!-- BLOCKS:START — всё между этими маркерами обслуживают scripts/plan/*.sh; не перемещайте и не удаляйте маркеры -->

## БЛОК 01 — Интеграция фронтенда с бэкендом (auth, кабинет, подписка)

**Статус:** [~] · **Заведён:** 2026-07-25 · **Ветка:** `feature/frontend-integration`

**Проблема.** Data-слой фронта (`models/{auth,user,payment}/` — Zod-схемы, axios-сервисы, React Query хуки), axios с инъекцией JWT + авто-refresh, `next.config.mjs`-прокси `/api → :8000` и бэковые эндпоинты auth — всё написано и по контрактам совместимо (JSON = snake_case, совпадает с Zod). Но «последняя миля» не сделана: формы login/register — статичные `<form>` без `onSubmit`/state; ни один хук `models/*` не вызывается в `app/`; Effector-сторы `$isAuth`/`$user` нигде не используются; страницы кабинета/подписки показывают захардкоженные данные. Задача — соединить готовый data-слой с готовой вёрсткой.

### Фаза 0 — верификация бэка *(готово)*
- [x] 2026-07-25 Модели, миграции, старт uvicorn проверены — бэк исправен (мнимый баг `indexed=True` не подтвердился, в коде `index=True`).
- [x] 2026-07-25 Auth-flow подтверждён руками: `POST /api/auth/register` → 201, `/login` → 200, `GET /api/users/me` с Bearer → 200. JSON = snake_case. `/users/me/subscription` без подписки → **404** (учесть в кабинете).

> **Статус реализации (2026-07-25):** весь код Фаз 1–4 написан и прошёл адверсариальное статическое ревью 6 агентами (типы/компиляция и контракты — 0 находок; финал: «ship-with-nits»). ⚠️ **Frontend НЕ собран:** `npm install` заблокирован (нет сети/permission), `node_modules` отсутствуют → `npm run build/lint` и frontend-тесты в этой сессии не запускались. Код помечен `[x]`, но DoD-сборка — `[!]` (см. ниже).

### Фаза 1 — авторизация end-to-end
- [x] 2026-07-25 `app/login/page.tsx` → react-hook-form + `loginRequestSchema` + `useLogin()`, обработка ошибки 401, редирект на `/account`.
- [x] 2026-07-25 `app/register/page.tsx` → rhf + клиентская схема поверх `registerRequestSchema` (confirm-пароль + согласие только на клиенте; пароль min 6; отправляются только контрактные поля). Авто-вход после регистрации.
- [x] 2026-07-25 Auth-состояние: стор переписан (`$isAuth`/`$authReady`, `setAuth`/`authHydrated`), новый `AuthProvider` гидратит из localStorage + кросс-таб `storage`-sync; `useLogin/useRegister` → `setAuth(true)`, `useLogout` → `setAuth(false)`.

### Фаза 2 — Header + защита маршрутов
- [x] 2026-07-25 `Header` переписан: сам вычисляет вход из `$isAuth`+`useMe`, реальный `useLogout()`, ссылки Кабинет/Админка; пропы `navCta/showProfileIcon/adminBadge` убраны со всех 10 страниц.
- [x] 2026-07-25 Guard `RequireAuth` (shared, чистый) на `/account`, `/subscription`; для `/admin` — новый виджет `RequireAdmin` (проверяет `is_admin`, не только вход). `failAuth()` в axios: терминальный 401 чистит токены + `setAuth(false)` + редирект.

### Фаза 3 — Личный кабинет на реальных данных
- [x] 2026-07-25 `account` на `useMe()`+`useSubscription()`+`useSearchHistory()`, состояния loading/empty, обработка 404 подписки. Фейковый блок «Недавно просмотренные» удалён (нет бэкенд-эндпоинта).
- [x] 2026-07-25 Созданы `account/settings` (правка профиля через `useUpdateMe`) и `account/history` (полная история) — битые ссылки сайдбара устранены. Общий `AccountSidebar` (usePathname) вместо 4× дублирования.

### Фаза 4 — Подписка/тарифы + оплата
- [x] 2026-07-25 `subscription` → `useSubscription()`, смена тарифа `useSubscribe()` (POST /payment/subscribe), отмена `useCancelSubscription()` с подтверждением. Фейковые «42/100» и «Visa 4242» удалены (нет бэкенда — см. вопросы).
- [x] 2026-07-25 `tariffs` → CTA зависит от входа (`$isAuth`): вошёл → `/subscription`, иначе `/register?plan=`.

### Проверка/DoD
- [!] **`npm run build && npm run lint` НЕ запущены** — заблокировано (нет `node_modules`, `npm install` отклонён). Нужно прогнать после `npm install`. Это единственный незакрытый пункт блока.
- [x] 2026-07-25 Backend-тесты: **17 passed** (unit 15 + integration 2). Попутно исправлен реальный баг тест-инфры (Блок 03): `tests/integration/conftest.py` вызывал `create_all` до импорта моделей → таблицы не создавались; добавлен `import src.main`.
- [x] 2026-07-25 Верификация — адверсариальное статическое ревью (6 агентов) вместо сборки; все находки-исправления применены (см. ниже).
- [ ] Ручные e2e-проверки через UI — занесены в `MANUAL_VERIFICATION.md` (не автотестуются; блокер — сборка + порт 8000).

**Исправлено по ревью:** `.btn-danger` добавлен в globals.css (был неопределён); `RequireAdmin` (админку видел любой залогиненный); `failAuth()` в axios (терминальный 401 не сбрасывал состояние); `<Image unoptimized>` для SVG-логотипа; alias-импорты (`payment/schema`, `app/page`); localize `Plan` в `format.ts` (убрана инверсия слоёв shared→models).

**Осознанно НЕ сделано (обоснование):** проверку exp access-токена в `AuthProvider` не добавляли — токены живут 15 мин, сброс по exp разлогинивал бы каждые 15 мин и ломал refresh; вместо этого — презенс-гидрация + серверная сверка через `failAuth`/`useMe` 401.

**Открытые вопросы (ответить в конце сессии):**
1. **Backend logout — заглушка (security).** `/auth/logout` не блэклистит refresh-токен (хотя `/refresh` blacklist проверяет) → украденный refresh валиден ~30 дней после «выхода». Фикс требует менять контракт logout (передавать refresh_token) — не делал, т.к. это backend-хардненинг вне «склейки». Делать?
2. **Способ оплаты и счётчик «использовано N/100»** — на бэке нет эндпоинтов. Фейковые данные удалил. Нужны ли эти фичи (тогда — отдельный backend-блок)?
3. **Порт 8000 занят** проектом `axidi` — фронт-прокси смотрит на `:8000`. Для e2e освободить 8000 или временно перенаправить прокси на `:8001`?
4. **Frontend-TDD (Vitest)** — не поднимал: без `node_modules` тесты не запустить. Ставить тест-раннер отдельным блоком?

**Мелкие нити (не блокеры, оставлены):** внутренние ссылки через `<a href>` вместо `<Link>` на статических mock-страницах (search/product/tariffs breadcrumbs); focus-ring `shadow-[…#141413]` хардкодом во всех инпутах (pre-existing, = токен slate); `bg-success-soft` в product (pre-existing mock, токен не определён).

## БЛОК 04 — Docker бэкенда и финализация деплоя

**Статус:** [ ] · **Заведён:** 2026-07-25 · **Источник:** `docs/sprints/sprint-001-backend-api.md` §1.7

**Проблема.** Спринт 1 фактически закрыт, но остаток из 1.7 не сделан: у бэкенда нет `Dockerfile`, сервис `backend` не добавлен в `docker-compose.yml` (сейчас там только postgres + redis), эндпоинты не прогнаны вручную.

- [ ] `backend/Dockerfile` — `python:3.11-slim` + poetry install + `uvicorn src.main:app`
- [ ] Добавить сервис `backend` в `docker-compose.yml` (`depends_on: postgres, redis`, env из `.env`, порт 8000)
- [ ] Прогнать все эндпоинты вручную (curl/httpx) → зафиксировать в `MANUAL_VERIFICATION.md`
- [ ] Проверить сборку и подъём всё-вместе: `docker build` + `docker compose up` (pg + redis + backend)

## БЛОК 05 — Fuzzy-поиск (pg_trgm) для тарифа advanced

**Статус:** [ ] · **Заведён:** 2026-07-25 · **Источник:** `docs/sprints/sprint-001-backend-api.md` §1.5 (остаток)

**Проблема.** Поиск в `products/service/product_service.py` умеет только точное + `ILIKE`-совпадение по `normalized_name`. Обещанный тарифу `advanced` fuzzy-поиск (pg_trgm) не реализован.

- [ ] Миграция alembic: `CREATE EXTENSION pg_trgm`
- [ ] GIN-индекс по `Product.normalized_name` (`gin_trgm_ops`)
- [ ] `similarity()`-поиск в `product_service` для плана `advanced` (fallback на ILIKE для `basic`/`trial`)
- [ ] Гейтить fuzzy по подписке через `middleware/subscription_guard`
- [ ] Проверить релевантность на реальных данных → `MANUAL_VERIFICATION.md`

## БЛОК 06 — Каркас парсеров: утилиты, исключения, ParserService

**Статус:** [ ] · **Заведён:** 2026-07-25 · **Источник:** `docs/sprints/sprint-001-backend-api.md` §2.1, §2.7

**Проблема.** В `modules/parser/service/` есть только `base.py`; отдельных утилит/исключений нет, а контроллер (`GET ""`, `POST /run`) — заглушка без реальной логики upsert и записи истории цен.

- [ ] `parser/service/exceptions.py` — `ParserError` / `ParserConnectionError` / `ParserParseError` / `ParserAuthError`
- [ ] `parser/service/utils.py` — `normalize_name`, `parse_price` («4 500 ₽» → Decimal), `safe_request` (retry + backoff), `compare_products`
- [ ] `ParserService` — `register` / `get` / `list_parsers` / `run_all` (asyncio.gather) / `run_one`
- [ ] Upsert по `(store_id, external_id)`; при изменении цены — запись в `PriceHistory`
- [ ] Заменить заглушки контроллера парсера на реальную логику (статус + запуск)
- [ ] Redis: `parser:status:{slug}`, `parser:lock:{slug}` (анти-двойной-запуск)

## БЛОК 07 — Пять парсеров магазинов

**Статус:** [ ] · **Заведён:** 2026-07-25 · **Источник:** `docs/sprints/sprint-001-backend-api.md` §2.2–2.6

**Проблема.** Ни один из 5 магазинных парсеров не реализован; в зависимостях есть только `httpx` (нет `beautifulsoup4`, `lxml`, `tenacity`). Зависит от БЛОКА 06.

- [ ] Зависимости: `beautifulsoup4`, `lxml`, `tenacity` в `requirements.txt` + `pyproject.toml`
- [ ] ТГСМ — `taggsm.ru` (HTML/bs4)
- [ ] Профи — `siriust.ru` (XHR/JSON API, иначе HTML)
- [ ] Либерти — `liberti.ru` (JSON API/HTML, sitemap.xml)
- [ ] Гринспарк — `green-spark.ru` (HTML)
- [ ] Дивизион — `divizion126.ru` (HTML)
- [ ] CSS-селекторы вынести в конфиг парсера; реальный скрейп каждого магазина → `MANUAL_VERIFICATION.md`

## БЛОК 08 — Планировщик и очередь (arq worker)

**Статус:** [ ] · **Заведён:** 2026-07-25 · **Источник:** `docs/sprints/sprint-001-backend-api.md` §2.8

**Проблема.** Нет фонового запуска парсеров: отсутствуют `scheduler`/`worker`, `arq` не в зависимостях. Зависит от БЛОКОВ 06–07.

- [ ] Зависимость `arq`; `backend/src/worker.py` — arq worker на Redis
- [ ] Расписание: каталог ежедневно 03:00; цены каждые 6 ч; приоритетные товары — раз в час
- [ ] Локи `parser:lock:{slug}` от параллельного запуска
- [ ] Изоляция ошибок: падение одного парсера не роняет остальные

## БЛОК 02 — Ядро данных: канон, offers, справочники, матчинг

**Статус:** [ ] · **Заведён:** 2026-07-25 · **Ветка:** `feature/db-core` (создать)

**Проблема.** Текущее ядро (`products`) — плоское: одна таблица смешивает предложение магазина и идентичность товара, связь между магазинами — только через строку `normalized_name`. Нет оптовой цены (а опт есть у всех источников: Розница/Опт, Столичный/опт), наличие — только `bool` (теряем «Мало»/«2 шт.»/«Предзаказ»), нет `uniq(store_id, external_id)` (повторный парсинг плодит дубли), нет канона, справочников, очереди модерации. Это не даёт корректно сравнивать цены и матчить товары между магазинами. Таблицы `products`/`price_history` **пусты** (проверено: 0 строк) — реструктуризацию делаем сейчас, ДО того как парсеры (Этап 3) начнут писать данные, чтобы не рефакторить ядро повторно.

**Границы и пересечения (важно — этот блок фундамент для 05/06/07):**
- **Порядок:** выполняется ДО блоков 05/06/07 и переименовывает их цели: `normalized_name`→`store_offers.normalized_title`, `PriceHistory`→`offer_price_history`, `(store_id, external_id)`→`(store_id, source_sku)`. **Не начинать 05/06/07 до закрытия 02**; после — актуализировать их формулировки под новые имена.
- **С Блоком 05 (pg_trgm):** расширение `pg_trgm` + GIN-trgm заводятся ЗДЕСЬ (таблицы новые, индексы — часть core-миграции). Блок 05 **не дублирует** `CREATE EXTENSION`/GIN — он лишь добавляет `similarity()`-логику и гейтинг по подписке, указывая на `store_offers.normalized_title`.
- **С Блоком 06 (парсеры):** схема ЗДЕСЬ (констрейнт `uniq(store_id, source_sku)`, новые колонки). Сам upsert-метод, запись истории цен и расширение `ParseResult` — в Блоке 06 (логика поверх этой схемы). Не дублировать.
- НЕ трогает Блок 01 (фронт/auth/кабинет/подписка). `users`/`subscriptions`/`stores` — не меняем; `search_history` — только `filters` JSON→JSONB.
- `categories` (публичный `/api/categories`) — **оставляем как есть**; таксономию парсинга вводим отдельной `part_types`, конвергенцию откладываем.

### Фаза 0 — Инфраструктура схемы и техдолг
- [ ] `naming_convention` в `Base.metadata` (`src/database.py`) — стабильные имена констрейнтов для будущих autogenerate.
- [ ] Расширения PG в миграции (`op.execute`): `pg_trgm`, `citext`.
- [ ] `search_history.filters` → `JSONB` (модель + миграция).
- [ ] `planenum` в этом блоке НЕ трогаем (замена нативного enum — отдельным блоком).

### Фаза 1 — Справочники (reference data)
- [ ] Модели `brands, devices, device_aliases, part_types, part_type_synonyms, quality_tiers, quality_tier_synonyms, colors, stopwords` (модуль `src/modules/catalog/model/`).
- [ ] Регистрация всех новых моделей в `alembic/env.py`.
- [ ] Идемпотентный сид: типы деталей (display/battery/…), классы качества (original/oem_hq/copy/service/unknown) + синонимы, топ-бренды/устройства.

### Фаза 2 — Ядро (offers / канон / история / модерация)
- [ ] `products` → переименовать в `store_offers`; добавить `price_opt, price_old, stock_status(varchar+CHECK), stock_qty, raw jsonb, is_active, match_status, match_confidence, first_seen_at/last_seen_at/price_changed_at, product_id(FK канон, SET NULL)`; **`uniq(store_id, source_sku)`**.
- [ ] Новая `products` (КАНОН): `cluster_id, quality_tier_id, brand_id, key_attrs jsonb, canonical_key(uniq), canonical_name`.
- [ ] `clusters` (`device_id`, `part_type_id`, uniq, кэш-агрегаты `offers_count/min_price_*`).
- [ ] `price_history` → `offer_price_history` (+`price_opt`, `stock_status`, FK на offer).
- [ ] `match_candidates` (очередь модерации: offer↔product, `score`, `features` jsonb, `status`, `decided_by/at`).
- [ ] Индексы: GIN trgm (`store_offers.normalized_title`, `products.canonical_name`, синонимы), partial `price_retail WHERE is_active`, FK-индексы.

### Фаза 3 — Миграция Alembic
- [ ] Переопределить модели, обновить импорты в `env.py`.
- [ ] `python -m alembic revision --autogenerate -m "core: offers/canonical/dictionaries/matching"` (down_revision = `fb0762d20565`).
- [ ] **Дописать руками то, что autogenerate не видит:** `CREATE EXTENSION`, `CHECK`-констрейнты статусов, GIN trgm, partial-индексы.
- [ ] `upgrade head` → `downgrade base` → `upgrade head` — проходит чисто.

### Фаза 4 — Адаптация существующих модулей (чтобы бэкенд компилировался)
- [ ] Перевести модули `products`/`search` (service/schema/controller) на `store_offers`+канон — только чтобы `uvicorn` стартовал (полноценные эндпоинты каталога/сравнения — отдельным блоком).
- [ ] НЕ здесь: `ParseResult`, upsert-логика, запись истории цен — это Блок 06 (использует схему из этого блока).

### Проверка/DoD
- [ ] `python -m alembic upgrade head` на чистой БД + round-trip down/up — без ошибок.
- [ ] Модели импортируются, `uvicorn src.main:app` стартует, `/api/health` → 200.
- [ ] Ручная вставка offer с `price_opt` и `stock_status='low'`; вставка дубля `(store_id, source_sku)` → нарушение uniq (констрейнт работает).
- [ ] Ручные проверки → `MANUAL_VERIFICATION.md`.

**Известные риски/заметки:**
- autogenerate НЕ генерирует extensions/CHECK/GIN-trgm/partial — обязательны ревью и ручная дописка ревизии.
- Переименование `products`→`store_offers` ломает текущие `products`/`search` модули и цели блоков 05/06/07 — правятся в Фазе 4; данных нет (0 строк), риск низкий.
- Порт БД в среде — `5434` (`backend/.env`), в `.env.example` — 5432; миграции гонять на реальный порт.
- Конвергенция `categories`↔`part_types` намеренно отложена, чтобы не задеть публичный `/api/categories` и Блок 01.

## БЛОК 03 — Покрытие тестами (pytest: unit + integration, TDD)

**Статус:** [~] · **Заведён:** 2026-07-25

**Проблема.** У проекта нет тестового набора (см. `CLAUDE.md`), поэтому вся регрессия ловится руками через `MANUAL_VERIFICATION.md`. Нужен базовый каркас автотестов и дисциплина TDD для нового кода, чтобы бизнес-логику (auth/JWT, цены/подписки, гейтинг, нормализация парсеров, кэш) можно было проверять быстро и повторяемо.

**Стандарт, которого держимся (test pyramid, 2025).** Широкое основание быстрых **unit**-тестов чистой логики → умеренный слой **integration** (сервис + реальная БД/Redis) → тонкая верхушка **API/e2e**. Избегаем «ice-cream cone» (перекос в медленные сквозные тесты). Тестируем **поведение и контракты**, а не реализацию.

**Что покрываем (высокая отдача):**
- Auth: hash/verify пароля, JWT round-trip/тип/подпись/срок, `get_current_user`/`get_current_admin` (401/403).
- Деньги и доступ: таблица цен планов, `create_subscription` (деактивация прежней, срок trial=10/paid=30 дн), `require_active_subscription` (403 без подписки) — прямая связка с `MANUAL_VERIFICATION` «показанная цена == списанная», «гейтинг по тарифу».
- Парсеры: `normalize_name`, `parse_price` («4 500 ₽» → Decimal), `ParserManager`, upsert по `(store_id, external_id)` + запись `PriceHistory` при смене цены (когда появятся, Блоки 06–07).
- Инфраструктура: `RateLimitMiddleware` (окно/429), `RedisCache` (TTL, сериализация, отсутствие устаревшей цены после инвалидации).
- API-контракты ключевых эндпоинтов auth/users/products/search (коды, форма JSON).

**Что НЕ покрываем (низкая отдача / чужая ответственность):** тривиальные геттеры и `__repr__`; сериализацию самого Pydantic/SQLAlchemy; сторонние библиотеки (passlib, jose, FastAPI-роутинг как таковой); автогенерённые Alembic-ревизии; чистую вёрстку без логики; реальные сетевые скрейпы магазинов (нестабильны — остаются в `MANUAL_VERIFICATION`).

**Границы.** Блок не меняет прод-код (кроме `requirements-dev.txt`); тесты не коммитятся в общую БД (отдельная `bscout_test`). Пересечений с Блоками 01/02/06–08 нет — тесты добавляются поверх их результатов по мере готовности.

### Фаза 0 — Каркас и разделение слоёв *(готово)*
- [x] 2026-07-25 Инструментарий: `pytest`, `pytest-asyncio`, `pytest-cov` в `backend/requirements-dev.txt`; `backend/pytest.ini` (`asyncio_mode=auto`, маркеры `unit`/`integration`, `--strict-markers`).
- [x] 2026-07-25 Структура с изоляцией нагрузки: `backend/tests/{unit,integration}/` — `unit` без внешних сервисов (всегда зелёные и быстрые), `integration` требует Postgres/Redis. Запуск раздельно: `pytest tests/unit` vs `pytest tests/integration`.
- [x] 2026-07-25 `tests/integration/conftest.py`: движок на отдельную `bscout_test` (или `TEST_DATABASE_URL`), create/drop таблиц, фикстуры `db_session` и `client` (ASGITransport + override `get_db`); **graceful skip**, если БД недоступна.
- [x] 2026-07-25 Seed-тесты (TDD-каркас, 17 зелёных): unit — пароли, JWT, `ParserManager`, `config`-URL, цены планов; integration — register→login→tokens, `/api/users/me` без токена → 401/403.

### Фаза 1 — Unit: чистая бизнес-логика (`tests/unit/`)
- [ ] Парсер-утилиты `normalize_name` / `parse_price` / `compare_products` — по мере появления (Блок 06); таблица кейсов формата цены и нормализации имён.
- [ ] `RateLimitMiddleware`: до лимита — пропуск, на `max_requests+1` в окне — 429, очистка окна по времени (инстанс + mock `call_next`, монотонное «время» через подмену).
- [ ] Валидация Pydantic-схем там, где есть нетривиальные правила (пароль min 6, границы длин) — только собственные правила, не движок.

### Фаза 2 — Integration: сервисы + реальная БД (`tests/integration/`)
- [ ] `auth.service`: `create_user` (хэш в БД, uniq email → ошибка), `authenticate_user` (успех/неверный пароль/нет юзера).
- [ ] `PaymentService.create_subscription`: деактивация прежней активной, срок trial=10 / paid=30 дней, `cancel_subscription` снимает `is_active`+`auto_renew`.
- [ ] `SearchHistoryService`: `record` пишет строку, `get_by_user` отдаёт по убыванию времени с лимитом.
- [ ] `RedisCache` против реального Redis: set/get с TTL, JSON-round-trip, `delete`/`exists`; сценарий «после инвалидации не отдаёт старую цену».
- [ ] Зависимости доступа: `get_current_user` (нет/неактивный юзер → 401), `require_active_subscription` (нет активной → 403).

### Фаза 3 — API/e2e (тонкий слой, `tests/integration/`)
- [ ] Auth-flow расширить: refresh-ротация, logout, повторный refresh после logout (учесть, что logout на бэке — заглушка).
- [ ] Products/search: пустой каталог → 200 + пустой список; поиск пишет `SearchHistory`; гейтинг fuzzy по тарифу (после Блока 05).
- [ ] Admin: доступ только `is_admin` (403 обычному пользователю).
- [ ] Негативные контракты: 422 на некорректном теле, 404 на отсутствующих ресурсах.

### Фаза 4 — Фронтенд (по готовности Блока 01)
- [ ] Vitest + `@testing-library/react` + jsdom (devDeps `frontend/`), скрипт `npm run test`.
- [ ] Unit: Zod-схемы `models/*/schema.ts` (parse/refine), `cn()`/утилиты, редьюсеры Effector-сторов.
- [ ] Компонентные: формы login/register (валидация, submit, обработка 401) с замоканным axios.
- [ ] MSW для мока API в хуках React Query (без реального бэка).

### Фаза 5 — Покрытие и CI-гейт
- [ ] `pytest --cov=src --cov-report=term-missing`; зафиксировать стартовый порог (ориентир ≥60% по `service/` и `middleware/`, не гнаться за 100%).
- [ ] Документировать команды запуска (unit / integration / coverage) — короткий раздел, куда решим (не плодить README без нужды).
- [ ] (Опционально) CI-workflow: поднять postgres+redis сервисами, `pytest tests/unit` всегда + `tests/integration` при доступной БД.

### Проверка/DoD
- [ ] `pytest tests/unit` — зелено без внешних сервисов; `pytest` целиком — зелено при поднятых Postgres/Redis (`docker compose up -d` + БД `bscout_test`).
- [ ] Новый код добавляется по TDD (red → green → refactor); каждый новый сервис/утилита приходит с тестом в том же PR.
- [ ] То, что автотестом не подтвердить (реальные скрейпы, «цена показана == списана» на живом флоу), — синхронно отражается в `MANUAL_VERIFICATION.md`.

**Известные заметки среды:**
- Postgres на хосте — порт **5434**; тест-БД `bscout_test` создаётся отдельно (`CREATE DATABASE bscout_test`), прод-данные не трогаются.
- Реальная схema auth-эндпоинтов — **snake_case** (`full_name`, `access_token`), несмотря на заявленный в `CLAUDE.md` camelCase; у `RegisterRequest`/`TokenResponse` нет alias-конфига. Тесты идут по факту; выравнивание конвенции — вне этого блока.
- `pytest-asyncio`: async-фикстуры — function-scope (иначе ScopeMismatch с event loop).

<!-- BLOCKS:END -->

---

## История обновлений

- 2026-07-25 — Наполнен Блок 02 (Ядро данных: канон/offers/справочники/матчинг). Подтверждено: таблицы `products`/`price_history` пусты (0 строк) → реструктуризация чистая, до парсеров. Целевая схема (offer↔канон, справочники, `clusters`, `match_candidates`, опт-цена, enum-наличие, `uniq(store_id, source_sku)`) сверена со стандартами. Зафиксированы границы с блоками 05 (pg_trgm/GIN заводятся в 02) и 06 (upsert/`ParseResult` остаются в 06); 02 идёт ДО 05/06/07 и переименовывает их цели. Активный блок остаётся 01.
- 2026-07-25 — Заведён Блок 03 (покрытие тестами) [~]: по стандарту test-pyramid составлен план unit/integration/e2e/фронт/CI. Развёрнут каркас `backend/tests/{unit,integration}/` (pytest + pytest-asyncio + cov, маркеры, изоляция слоёв, тест-БД `bscout_test`, graceful skip) — 17 seed-тестов зелёные. Активный блок остаётся 01.
- 2026-07-25 — Внесены блоки 04–08 (добор бэкенда по итогам сверки со Спринтом 1–2: Docker, fuzzy pg_trgm, каркас парсеров, 5 парсеров, arq-планировщик). В INDEX добавлена строка `S1` [x] (Спринт 1 закрыт) и строка Блока 02. Источник задач — `docs/sprints/sprint-001-backend-api.md`.
- 2026-07-25 — Блок 01: реализованы Фазы 1–4 (auth e2e, Header+guards, кабинет+settings+history, подписка/тарифы). ~20 файлов фронта. Адверсариальное ревью 6 агентами (types/contracts — 0 находок), находки исправлены (RequireAdmin, failAuth, .btn-danger, unoptimized, alias). Backend-тесты 17 passed + починен баг тест-инфры (integration conftest). Не закрыт DoD: `npm run build/lint` (нет node_modules). Вопросы — в секции блока.
- 2026-07-25 — Заведён Блок 01 (интеграция фронта с бэком). Фаза 0 (верификация бэка) закрыта: auth-flow подтверждён руками на `:8001`, JSON snake_case, подписка без данных → 404. Ветка `feature/frontend-integration`.
- 2026-07-25 — Инициализирована система планирования (MASTERPLAN + INDEX + archive + MANUAL_VERIFICATION + `scripts/plan/` + SessionStart-хук).
