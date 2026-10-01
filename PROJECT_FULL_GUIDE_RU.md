# BScout — Полный гайд для начинающего (как для ребёнка, но точно по коду)

> Файл: `./PROJECT_FULL_GUIDE_RU.md` (корень).
> Аудитория: начинающий разработчик. Стиль: сначала — объяснение «на пальцах», в скобках — точный термин.
> Все пути — реальные, проверены по репозиторию. Секретов здесь нет, только шаблоны из `.env.example` / `.env.prod.example`.

**Оглавление**

1. [Что такое BScout в 5 предложениях + схема](#1-что-такое-bscout-в-5-предложениях--схема)
2. [Стек: таблица с аналогиями и «почему именно это»](#2-стек-таблица-с-аналогиями-и-почему-именно-это)
3. [Карта папок: что где лежит и что будет если удалить](#3-карта-папок-что-где-лежит-и-что-будет-если-удалить)
4. [Страшные слова простыми словами: infra, nginx, Docker, Postgres, Redis, Celery](#4-страшные-слова-простыми-словами-infra-nginx-docker-postgres-redis-celery)
5. [Парсеры: как устроены и где их конфиги](#5-парсеры-как-устроены-и-где-их-конфиги)
6. [Сквозной пример: от клика до базы и обратно](#6-сквозной-пример-от-клика-до-базы-и-обратно)
7. [Бэкенд по косточкам](#7-бэкенд-по-косточкам)
8. [Фронтенд по косточкам](#8-фронтенд-по-косточкам)
9. [Разбор ключевых файлов построчно](#9-разбор-ключевых-файлов-построчно)
10. [Конфиги и переменные окружения](#10-конфиги-и-переменные-окружения)
11. [Запуск локально + проверка + частые ошибки](#11-запуск-локально--проверка--частые-ошибки)
12. [Словарь 30 терминов](#12-словарь-30-терминов)
13. [FAQ: 10 «глупых» вопросов](#13-faq-10-глупых-вопросов)
14. [Что учить дальше](#14-что-учить-дальше)
15. [Выводы, допущения, проверено](#15-выводы-допущения-проверено)

---

## 1. Что такое BScout в 5 предложениях + схема

1. BScout — это сайт-агрегатор цен на запчасти для телефонов и ноутбуков в городе Ставрополь (как Яндекс.Маркет, но только по 4–5 местным магазинам).
2. Роботы-парсеры ночью ходят по сайтам магазинов, копируют названия и цены в нашу базу данных.
3. Пользователь вводит «дисплей iPhone 13» в поиск, а сайт показывает таблицу «где дешевле» и подсвечивает самую низкую цену.
4. Доступ платный по подписке: Пробный (0 ₽) / Базовый (399 ₽) / Продвинутый (499 ₽), вход — по email+пароль с JWT-токенами.
5. Внутри два приложения: витрина на Next.js и API на FastAPI, плюс базы Postgres + Redis, фоновые задачи Celery и охранник Nginx.

**Схема движения запроса (прод):**

```text
Браузер пользователя
   |  https://bscout.ru/search?q=дисплей
   v
Nginx (deploy/nginx/nginx.conf + bscout.conf.template)
   |-- /  (без /api)  --> frontend:3000 (Next.js, отдаёт HTML)
   |-- /api/* ---------> backend:8000 (FastAPI, отдаёт JSON)
   |-- лимиты: auth 2r/s, api 20r/s, max body 2m
   v
Backend src/main.py
   |-- RateLimitMiddleware + RequestIdMiddleware + CORS
   |-- router: auth/users/products/search/stores/parser/tracking/...
   v
   |-- Postgres (долгая память: users, offers, цены) <-- SQLAlchemy async
   |-- Redis (быстрая память: кэш поиска 5 мин, локи parser:lock, очередь Celery)
   v
Worker/Beat (src/worker.py + src/celery_app.py)
   |-- sync_catalog 03:00, sync_prices 07:30/13:30/19:30, expire_subscriptions ежечасно
```

**Локально (dev) проще:** `docker-compose.yml` поднимает только `postgres + redis + backend + worker + beat + flower`. Фронт запускается руками `npm run dev` на :3000, Nginx в деве не используется (его заменяет прокси Next.js `/api -> localhost:8000`).

Проверено: `README.md`, `DESIGN.md`, `docs/technical-specification.md`, `docker-compose.yml`, `docker-compose.prod.yml`, `deploy/nginx/nginx.conf`.

---

## 2. Стек: таблица с аналогиями и «почему именно это»

Как читать: «Что это» — по-детски. «Аналог» — чем можно заменить. «Почему это» — причина выбора в этом проекте.

| Технология (где лежит) | Что это простыми словами | Жизненная аналогия | За что отвечает здесь | Аналоги | Почему выбрано именно это |
|---|---|---|---|---|---|
| Python 3.11 (`backend/`) | Язык, на котором написан бэкенд | Русский язык для повара | Вся логика API | Node, Go, PHP | У команды Python-опыт + богатые библиотеки парсинга (BeautifulSoup, httpx) |
| FastAPI (`backend/src/main.py`) | Каркас для API (принимает HTTP, отдаёт JSON) | Официант: принял заказ, отнёс на кухню | Роутеры `/api/*`, валидация через Pydantic, Swagger | Django REST, Flask, NestJS | Быстрый, async из коробки, автодокументация `/docs` |
| Uvicorn (`backend/Dockerfile` CMD) | Сервер, который запускает FastAPI | Двигатель машины | `uvicorn src.main:app --workers 2 --proxy-headers` | Gunicorn, Hypercorn | Стандарт для ASGI/async Python |
| SQLAlchemy 2.0 async + asyncpg (`backend/src/database.py`) | Переводчик «Python-объекты <-> SQL-таблицы» | Переводчик с русского на складской | Модели `User`, `StoreOffer`, сессии `get_db()` | Django ORM, Prisma, raw SQL | Async = держит много запросов без блокировки; миграции через Alembic |
| Alembic (`backend/alembic/`, `alembic.ini`) | История изменений базы (как git для таблиц) | Журнал перепланировок склада | `alembic upgrade head`, таблица `alembic_version` | Django migrations, Prisma migrate | Стандарт для SQLAlchemy |
| PostgreSQL 16 (`postgres` сервис) | Главная надёжная база (таблицы на диске) | Большой склад с полками и картотекой | users, offers, цены, подписки, история | MySQL, SQLite, Mongo | Нужны связи + триграммный поиск `pg_trgm` + JSONB; SQLite не тянет прод |
| Redis 7 (`redis` сервис, `backend/src/modules/cache/service/redis_cache.py`) | Сверхбыстрая память-записка (всё в RAM) | Доска-стикер у кассы | Кэш поиска TTL 5 мин, `parser:lock:*`, `parser:status:*`, rate-limit счётчики, брокер Celery | Memcached, in-memory dict | Умеет и кэш, и очередь, и локи с TTL в одном флаконе |
| Pydantic v2 + pydantic-settings (`backend/src/config.py`, `*/schema/`) | Проверяльщик форм: «email похож на email?» | Охранник на входе с линейкой | Схемы запросов/ответов, класс `Settings` читает env | Marshmallow, Zod (на фронте) | Строгая типизация + понятные 422 ошибки |
| python-jose + passlib/bcrypt (`backend/src/modules/auth/`) | Паспортный стол + сейф для паролей | Паспорт + отпечаток пальца | JWT access 15 мин + refresh 30 дней, `password_hash` | Auth0, Firebase Auth | Своё = бесплатно и без внешней зависимости; bcrypt нельзя «расшифровать» |
| httpx + BeautifulSoup4 + lxml (`backend/src/modules/parser/`) | Ложка+лупа для чтения чужих сайтов | Библиотекарь переписывает ценники конкурентов | `safe_request` с ретраями, `parse_product_html` по селекторам | Scrapy, Playwright, aiohttp | Лёгкие, async, хватает для статичного HTML; Playwright тяжёлый и палевный |
| Celery + Beat + Flower (`backend/src/celery_app.py`, `src/worker.py`) | Ночные уборщики по расписанию | Заводской гудок + бригада | `sync_catalog` 03:00, `sync_prices` 3 раза/день, `expire_subscriptions`, мониторинг Flower :5555 | ARQ, RQ, Cron+скрипты | Раньше был ARQ (см. `MIGRATION_ARQ_TO_CELERY.md`), перешли на Celery ради Flower, ретраев и привычного Beat |
| Next.js 14 App Router + React 18 (`frontend/src/app/`) | Каркас сайта (страницы + кнопки) | Конструктор LEGO для витрины | Роуты `/`, `/search`, `/account`, `/admin`, SSR/CSR | CRA, Vite, Nuxt | SSR для SEO + файловый роутинг + прокси `/api` |
| TypeScript (`frontend/**/*.ts(x)`) | Русский язык с проверкой ошибок до запуска | Черновик с корректором | Типы из Zod (`z.infer`), пропсы компонентов | Plain JS | Ловит опечатки в `snake_case` полях до прода |
| Tailwind CSS v3 + shadcn/ui + Radix (`frontend/tailwind.config.ts`, `src/shared/ui/`) | Готовые стили-кубики | Набор наклеек вместо рисования | Классы `flex gap-4`, токены `brand-dark #010D3E`, `accent #b8007b` | SCSS Modules, MUI, Bootstrap | Быстро + единый дизайн; Radix даёт доступность (клавиатура, скринридеры) |
| TanStack React Query (`frontend/src/models/*/hooks.ts`) | Умный блокнот: помнит ответы API | Дневник «уже спрашивал — вот ответ» | `useLogin`, `useMe`, `useParsers` с кэшем и `invalidateQueries` | SWR, Redux-Thunk | Кэш + refetch + optimistic из коробки |
| Axios (`frontend/src/shared/api/axios.ts`) | Почтальон фронтенда | Курьер с пропуском | `baseURL: '/api'`, вставляет `Bearer`, авто-refresh при 401 | fetch | Перехватчики (interceptors) удобнее голого fetch |
| Effector (`frontend/src/shared/config/store.ts`) | Тумблер «вошёл/не вошёл» | Выключатель света на весь дом | `$isAuth`, `setAuth`, кросс-таб sync | Redux, Zustand, Context | Только клиентское состояние (авторизован?), серверное — в React Query. Так не путаются |
| Zod + React Hook Form (`frontend/src/models/*/schema.ts`) | Проверка анкеты до отправки | Учитель проверяет домашку | `registerRequestSchema`, `loginRequestSchema` | Yup, Valibot | Одна схема = и подсказки в форме, и типы TS |
| Docker + Compose (`docker-compose.yml`, `docker-compose.prod.yml`, `backend/Dockerfile`, `frontend/Dockerfile`) | Коробки-контейнеры с готовым окружением | Ланчбоксы: везде одинаковый обед | Локально: postgres+redis; в проде: +backend+worker+beat+frontend+nginx+migrate | Podman, bare-metal | «У меня работает» исчезает: образ одинаковый везде |
| Nginx (`deploy/nginx/nginx.conf`, `infra/nginx/base-nginx.conf`) | Швейцар у двери: решает кого куда | Ресепшн в отеле | TLS, `client_max_body_size 2m`, gzip, `limit_req` 20r/s и 2r/s для auth, `/api/ -> backend`, `/ -> frontend` | Traefik, Caddy, Cloudflare | Лёгкий, стандарт де-факто, дешёвый TLS-терминатор |
| YooKassa [не проверено — заглушка] (`backend/src/modules/payment/`) | Касса для приёма денег | Кассовый аппарат | `POST /payment/subscribe`, webhook [заглушка подписи] | Stripe, CloudPayments | Российская касса, рубли, 54-ФЗ. Пока принимать деньги нельзя (см. MASTERPLAN Блок 12) |

Проверено: `README.md:57-102`, `backend/requirements.txt`, `frontend/package.json`, `backend/src/celery_app.py`, `backend/Dockerfile`, `MIGRATION_ARQ_TO_CELERY.md` (имя файла в корне).

---

## 3. Карта папок: что где лежит и что будет если удалить

### 3.1 Корень — «город»

| Папка/файл | Зачем (по-детски) | Ключевые файлы внутри | Что будет если удалить |
|---|---|---|---|
| `backend/` | Кухня: готовит JSON | `src/main.py`, `src/config.py`, `src/worker.py`, `requirements.txt`, `alembic/` | Умрёт всё API, фронт покажет скелеты |
| `frontend/` | Витрина магазина | `src/app/`, `src/models/`, `src/widgets/`, `src/shared/`, `next.config.mjs` | Нечего открыть в браузере |
| `infra/` | Чертежи для стройки (образцы, не прод) | `nginx/base-nginx.conf`, `docker/Dockerfile.*` (пустые [не проверено — файлы 0 байт]) | Ничего не упадёт сейчас, но новичку негде подсмотреть пример |
| `deploy/` | Боевые чертежи для прода | `nginx/nginx.conf` (боевой, 101 строка с комментами) | Прод-nginx не поднимется; локалка жива |
| `docs/` | Библиотека: ТЗ, планы, аудиты | `technical-specification.md`, `plan/MASTERPLAN.md`, `subscriptions.md`, `SECURITY_AUDIT.md` | Потеряем память проекта, код продолжит работать |
| `scripts/` | Кнопки-помощники | `ops/`, `plan/plan_status.sh`, `archive_block.sh` | Придётся всё делать руками |
| `docker-compose.yml` | Меню локальной столовой | сервисы `postgres, redis, backend, worker, beat, flower` | Не поднимется локальная связка |
| `docker-compose.prod.yml` | Меню ресторана (прод) | `+ migrate, frontend, nginx`, сети `edge/data`, лимиты CPU/RAM | Не задеплоить прод |
| `.env.example` / `.env.prod.example` | Бланк анкеты без ответов | 6 строк (dev) / 86 строк (prod) | Новичок не узнает какие переменные нужны |
| `DESIGN.md` | Книга стилей витрины | Токены цветов, FSD, правила `use client` | Фронт будет разношёрстным |
| `README.md` | Паспорт проекта | Архитектура, тарифы, быстрый старт | Непонятно как запускать |
| `AGENTS.md` (+ `backend/AGENTS.md`, `frontend/AGENTS.md`) | Правила для роботов-помощников | Команды, соглашения `snake_case`, MVC | Агенты начнут плодить мусор |

### 3.2 `backend/src/` — «кухня»

```text
backend/src/
  main.py           # дверь ресторана: создаёт FastAPI(), вешает middleware, include_router ×15
  config.py         # книга рецептов из env: Settings + database_url + redis_url
  database.py       # труба к складу: engine + async_session_factory + get_db()
  db_metadata.py    # список всех моделей для Alembic/тестов [не проверено детально]
  celery_app.py     # будильник: beat_schedule 5 задач
  worker.py         # бригады уборщиков: run_parser/sync_catalog/sync_prices/expire/...
  cli.py            # ручные команды [не проверено]
  logging_config.py # как пахнут логи
  middleware/       # досмотр на входе: rate_limit.py, request_id.py
  modules/          # цеха, каждый: model/ + schema/ + service/ + controller/
```

### 3.3 `frontend/src/` — «витрина» (FSD)

```text
frontend/src/
  app/        # улицы-маршруты: page.tsx, layout.tsx, login/, search/, account/, admin/...
  models/     # склады данных: <entity>/{schema.ts, service.ts, hooks.ts, index.ts} ×13
  widgets/    # большие витрины: Header, Footer, homeWidget, TariffPlans, TrackButton...
  shared/     # общие инструменты: api/axios.ts, config/store.ts, providers/, lib/utils.ts, ui/
  test/       # helpers для Vitest [не проверено детально]
```

### 3.4 `docs/`, `scripts/`, `infra/`, `deploy/`

- `docs/technical-specification.md` — ТЗ (648 строк): модели User/Subscription/Store/Product, 20+ эндпоинтов, fuzzy-поиск. Устарело местами (пишет React 19 + CRA, реально Next 14).
- `docs/plan/MASTERPLAN.md` — единственный живой план. Правило: не создавать `PLAN_*.md`. Активный блок 08 — «боевой обход магазинов».
- `docs/subscriptions.md`, `bussines-plan.md`, `parser-profi-plan.md`, `SECURITY_AUDIT.md`, `MATCHING_REALITY_CHECK.md`, `audit/`, `review/`, `sprints/` — история решений.
- `scripts/plan/*.sh` — `plan_status.sh`, `archive_block.sh`; `scripts/ops/` — операционные скрипты [не проверено детально].
- `infra/nginx/base-nginx.conf` — базовые настройки (gzip, таймауты, лимиты 20r/s). `infra/nginx/nginx.conf` — пустой (0 байт, видимо заглушка).
- `deploy/nginx/nginx.conf` — боевой конфиг с объяснениями на русском: зачем `client_max_body_size`, зачем две `limit_req_zone`.

Проверено: листинги `backend/src`, `frontend/src`, `infra/*`, `deploy/nginx`, `docs`, `scripts`; файлы `docker-compose*.yml`, `.env.example`, `.env.prod.example`, `MASTERPLAN.md:1-40`.

---

## 4. Страшные слова простыми словами: infra, nginx, Docker, Postgres, Redis, Celery

### Infra (инфраструктура) — «коммуникации дома»
Это не код сайта, а трубы, свет и охрана: где стоят базы, как ходит интернет, где лежат сертификаты. В коде — папки `infra/` (черновики) и `deploy/` + `docker-compose*.yml` (боевое). Без неё сайт работает только на твоём ноутбуке.

### Nginx — «швейцар-охранник»
Стоит первым, встречает интернет. Решает: картинку отдать самому или позвать повара (backend).

Что он делает в `deploy/nginx/nginx.conf` (построчно, по-детски):

- `worker_processes auto; worker_connections 4096` — «сколько рук у швейцара».
- `server_tokens off` — «не хвастайся версией, а то взломают».
- `log_format ... rt=$request_time` — «записывай кто приходил и как долго ждал».
- `gzip on` — «сжимай чемодан перед отправкой, чтобы летел быстрее».
- `client_max_body_size 2m` — «посылки больше 2 МБ не принимаем» (защита от забивания памяти uvicorn, нашёл аудит).
- `limit_req_zone ... api_zone rate=20r/s` и `auth_zone rate=2r/s` — «не чаще 20 стуков в секунду, а в дверь логина — не чаще 2» (второй рубеж после `RateLimitMiddleware` в Python).
- `include ... bscout.conf` — «а дальше читай список жильцов» (там `location / -> frontend:3000`, `location /api/ -> backend:8000`, редирект http->https).

Аналог: Traefik, Caddy (проще, но менее привычен), Cloudflare (чужой дядя). Выбран Nginx: стандарт, копеечный по ресурсам (256 МБ лимит), все умеют чинить.

### Docker — «ланчбоксы»
Проблема без него: «у меня работает, у тебя нет» (разный Python, нет Postgres). Решение: запаковать приложение + окружение в образ.

- `backend/Dockerfile` — двухэтажный: `builder` ставит `requirements.txt` в `/opt/venv`, `runtime` копирует только готовое, ставит `fonts-dejavu-core` (иначе кириллица в PDF — пустые квадратики), создаёт пользователя `app` (не root!), запускает `uvicorn ... --workers 2`. Миграции НЕ запускает (иначе 2 реплики подерутся за `alembic_version`).
- `docker-compose.yml` (dev): `postgres:16-alpine`, `redis:7-alpine`, `backend` (порт `${BACKEND_PORT:-8000}:8000`), `worker` (`celery worker`), `beat` (`celery beat`), `flower` (:5555). База хранится в томе `pgdata` (переживёт перезапуск).
- `docker-compose.prod.yml` (оверлей): порты баз СБРОШЕНЫ (`!reset []`), сеть `data` — `internal: true` (базы не видно из интернета), добавлен `migrate` (одноразово `alembic upgrade head`), `frontend` и `nginx` с TLS. Redis с `--maxmemory 256mb --maxmemory-policy volatile-lru` («выкидывай только стикеры с TTL, задачи не трогай»).

Аналог: ставить всё руками на сервер, Podman, Kubernetes (пушка по воробьям для MVP).

### Postgres — «склад»
Таблицы на диске, переживают выключение. Здесь: `users`, `subscriptions`, `stores`, `store_offers`, `offer_price_history`, `refresh_tokens`, история поиска, трекинг. Ходим через SQLAlchemy (`database.py`), меняем схему через Alembic. Порт 5432.

Аналог: MySQL (нет `pg_trgm` для fuzzy), SQLite (один файл, нет сети), Mongo (нет связей). Выбран Postgres: связи + триграммы + JSONB.

### Redis — «доска-стикеры»
Очень быстрый, но забывчивый (в основном в памяти). В BScout 4 работы:

1. **Кэш** — ответ поиска лежит 5 минут (`RedisCache.set(key, value, ttl=300)`). Не надо снова считать.
2. **Локи** — `parser:lock:tgsm = "1" nx ex 3600` («парсер уже бежит, второй не заходи»). Безлимит держит 6 часов (`FULL_SYNC_LOCK_TTL`).
3. **Статусы** — `parser:status:tgsm = {is_running, products_found, errors}` TTL 86400 (сутки), при постановке — 900 сек.
4. **Очередь Celery** — брокер и бэкенд (`broker=settings.redis_url`). Плюс счётчики rate-limit и чёрный список refresh-токенов.

Код: `backend/src/modules/cache/service/redis_cache.py` — `get/set/delete/exists/expire/acquire_lock(nx)/release_lock`. Аналог: Memcached (только кэш, без очередей).

### Celery (воркер + бит) — «ночные уборщики»
HTTP-запрос живёт секунды, а обход каталога — 3–4 часа. Нельзя делать это внутри запроса (nginx отдаст 504 через 60 сек — так и было до 2026-07-29!). Поэтому: запрос только КЛАДЁТ задачу в очередь (202 за 62 мс), а отдельный процесс-воркер её жуёт.

- `src/celery_app.py` — будильник: `sync_catalog 03:00`, `sync_prices 07:30/13:30/19:30`, `expire_subscriptions каждый час :05`, `cleanup_refresh_tokens 04:30`, `prune_history вс 04:45`.
- `src/worker.py` — бригады: `run_parser` (один магазин), `sync_catalog` (все, только если `PARSER_FULL_SYNC_ENABLED=true`), `sync_prices` (только отслеживаемые, лимит 500 + `AlertService.scan_for_drops`), `expire_subscriptions`, `cleanup_refresh_tokens`, `send_password_mail`, `send_broadcast`.
- Хитрость: Celery sync, а код async → `_run_async()` крутит свой event-loop.

Раньше был ARQ, перешли на Celery (см. `MIGRATION_ARQ_TO_CELERY.md` в корне): Flower-морда, ретраи, привычный Beat.

Проверено: `deploy/nginx/nginx.conf:1-101`, `infra/nginx/base-nginx.conf`, `docker-compose.yml`, `docker-compose.prod.yml:1-120`, `backend/Dockerfile`, `backend/src/celery_app.py`, `backend/src/worker.py`, `backend/src/modules/cache/service/redis_cache.py`, `backend/src/database.py`.

---

## 5. Парсеры: как устроены и где их конфиги

**Идея:** парсер — это робот-покупатель: открывает карту сайта (`sitemap.xml`), собирает ссылки на товары, открывает каждую карточку и переписывает «название — цена — наличие» в `ParseResult`, потом `ParserService` кладёт это в Postgres.

**Файлы:**

```text
backend/src/modules/parser/
  service/base.py          # контракт: class BaseParser(search, update_catalog) + ParseResult + ParserManager
  service/parser_service.py# дирижёр: локи, upsert_offer, run_one/run_isolated/run_all/enqueue_run
  service/parsers/__init__.py # список AVAILABLE_PARSERS + register_default_parsers()
  service/parsers/tgsm.py  # ТГСМ taggsm.ru (OpenCart, STORE_SLUG=tgsm)
  service/parsers/profi.py # Профи siriust.ru (CS-Cart, slug=profi, умеет опт+розницу)
  service/parsers/liberti.py # Либерти (Битрикс)
  service/parsers/divizion.py# Дивизион divizion126.ru (Битрикс)
  service/queue.py         # положить задачу в очередь (arq-наследие [не проверено детально])
  service/utils.py         # parse_price("4 500 ₽"->Decimal), normalize_name, safe_request
  controller/              # POST /api/admin/parsers/run -> 202 {job_id}, GET /status
  schema/                  # схемы запуска (full_sync, limit, section)
```

**Конфиги парсеров — это константы вверху каждого файла** (не .env!):

```python
# tgsm.py
STORE_SLUG = "tgsm"; DEFAULT_BASE_URL = "https://taggsm.ru"
REQUEST_TIMEOUT = 45.0   # ТГСМ медленный: 2 из 3 запросов падали на 25с
REQUEST_RETRIES = 4; REQUEST_BACKOFF = 1.5
CATALOG_CONCURRENCY = 2  # только 2 параллельных (вежливо!)
REQUEST_DELAY = 1.0      # пауза 1с между запросами
MAX_SITEMAP_DEPTH = 3
# profi.py: TIMEOUT 25.0, CONCURRENCY 4, DELAY 0.5 (побыстрее)
```

Плюс общие ручки в `parser_service.py`: `DEFAULT_RUN_LIMIT=500`, `LOCK_TTL=3600`, `FULL_SYNC_LOCK_TTL=21600`, `MIN_DEACTIVATION_COVERAGE=0.8`.

Плюс env-флаг в `.env*`: `PARSER_FULL_SYNC_ENABLED=false` — без `true` ночной `sync_catalog` ничего не трогает (защита от DDoS чужих сайтов).

**Как идёт обход (упрощённо):**

1. `collect_product_urls` — очередь `[(sitemap.xml, 0)]`, разбирает вложенные sitemap до глубины 3, `filter_product_urls` оставляет только товары (у ТГСМ — белый список `product_id=`, у Профи — чёрный список `/blog`, `/news`, `dispatch=`).
2. `_parse_many` — семафор (`asyncio.Semaphore(2..4)`) + `await asyncio.sleep(DELAY)` → `parse_product_html` → `ParseResult(source_sku, title, price_retail, stock_status, ...)`.
3. `ParserService.upsert_offer` — ищет `(store_id, source_sku)`: нет → INSERT + `OfferPriceHistory`, есть → UPDATE + новая строка истории если цена сменилась. В конце — `MatchingService.match_all` (склейка одинаковых товаров разных магазинов).
4. Деактивация (`_deactivate_stale_offers`) — только если прогон ПОЛНЫЙ и покрытие ≥80% (иначе один сбой потёр бы пол-каталога).

**Особенности магазинов (замер 2026-08-08, MASTERPLAN Блок 07):**

- ТГСМ: наличие ПО ФИЛИАЛАМ (33 филиала, Ставропольских 2). Глобальный «в наличии» врёт. Парсер кладёт `raw.branches` + `raw.stavropol`. Фильтр `section` не работает (все URL `index.php?...`).
- Профи: единственный с оптом (`price_opt`, 78/78 живых). Сортирует URL по глубине, добирает батчами (иначе категории забивали лимит).
- Либерти: опт только под логином (нет аккаунта — нет опта). Наличие читается только с карточки, не из листинга.
- Дивизион: самый урожайный (138 живых офферов).
- ГринСпарк: парсера НЕТ — сайт отдаёт бот-заглушку. Обход защиты не делаем (этика + закон).

Проверено: `base.py`, `parsers/__init__.py`, `tgsm.py:1-40,163-213`, `profi.py:1-40`, `parser_service.py:16-40,122-196,213-300`.

---

## 6. Сквозной пример: от клика до базы и обратно

Возьмём **регистрацию** (самая понятная цепочка, файлы реальные).

```text
1. Человек заполняет форму
   frontend/src/app/register/page.tsx
   -> react-hook-form + registerRequestSchema (из models/auth/schema.ts)
   -> проверяет: email похож на email, пароль ≥6, full_name не пустой

2. Клик «Зарегистрироваться»
   frontend/src/models/auth/hooks.ts : useRegister()
   -> mutationFn: authApi.register(data)

3. Почтальон несёт письмо
   frontend/src/models/auth/service.ts : authApi.register
   -> api.post('/auth/register', data)
   frontend/src/shared/api/axios.ts
   -> baseURL '/api', Content-Type json, токена ещё нет

4. Next.js-прокси (локалка) / Nginx (прод)
   next.config.mjs: /api/* -> http://localhost:8000 (локально :8010, см. .env)
   прод: nginx location /api/ -> backend:8000

5. Дверь бэкенда
   backend/src/main.py : app.include_router(auth_router)
   -> RequestIdMiddleware (даёт X-Request-ID)
   -> RateLimitMiddleware (auth: 10 запросов / 300 сек)
   -> CORSMiddleware (пускает только cors_origins())

6. Контроллер (официант принял заказ)
   backend/src/modules/auth/controller/*.py : POST /api/auth/register
   -> валидирует Pydantic-схемой, вызывает service.create_user

7. Сервис (кухня готовит)
   backend/src/modules/auth/service/*.py
   -> passlib/bcrypt хэширует пароль (в БД лежит только хэш!)
   -> INSERT users (email unique, иначе 409)
   -> создаёт Subscription plan=trial на 10 дней [по README; в ТЗ было 7 — расхождение]
   -> python-jose выдаёт access (15 мин) + refresh (30 дней), refresh кладёт в refresh_tokens

8. База (склад записал)
   backend/src/database.py : get_db() -> async_session_factory
   -> SQL: INSERT INTO users ...; INSERT INTO subscriptions ...
   -> commit, иначе rollback

9. Ответ обратно
   JSON {access_token, refresh_token, token_type} -> фронт
   hooks.ts onSuccess: localStorage.setItem оба токена, setAuth(true) (Effector),
   invalidateQueries(['user']) -> Header перерисуется в «Кабинет»
   -> редирект на /account

10. Следующий запрос уже с пропуском
    axios request-interceptor: Authorization: Bearer <access>
    backend get_current_user: проверяет подпись JWT + срок + отзыв в Redis
    401 протух -> response-interceptor: POST /api/auth/refresh -> повтор originalRequest
    refresh нет/битый -> failAuth(): чистит storage, setAuth(false), window.location='/login'
```

**Второй мини-пример — поиск товара:**

`app/search/page.tsx` -> `models/search/hooks.ts useSearch(q)` -> `service.ts GET /products?q=` -> `backend/src/modules/search/controller/search.py` -> `service` ищет по `normalized_name` (точное → ILIKE → для advanced fuzzy через `pg_trgm`) -> проверяет подписку `require_active_subscription` (нет → 403) -> кладёт `SearchHistory` -> кэширует в Redis на 5 мин -> `{results:[{..., is_cheapest:true}], total, page}` -> `widgets/searchWidget/SearchResults + ProductCard`.

Проверено: `frontend/src/models/auth/{schema,service,hooks}.ts`, `frontend/src/shared/api/axios.ts`, `backend/src/main.py`, `backend/src/config.py`, `docs/technical-specification.md:3.3`, `README.md:285-310`.

---

## 7. Бэкенд по косточкам

Правило проекта (`backend/AGENTS.md`): каждый фиче-модуль = `model/` (таблицы) + `schema/` (Pydantic) + `service/` (логика) + `controller/` (роутер `<name>_router`). Роутеры регистрируются в `src/main.py`. Модели — в `src/db_metadata.py`.

| Модуль (`src/modules/<name>/`) | Зачем (по-детски) | Главные файлы | С кем дружит |
|---|---|---|---|
| `health/` | Градусник: «я живой?» | `controller` → `GET /api/health` | Ни с кем; дёргают Docker-healthcheck и nginx |
| `auth/` | Паспортный стол | `model/user.py (User)`, `model/refresh_token.py`, `service/password_service.py`, `service/security.py (JWT)` | `users/` (профиль), `cache/` (блэклист), `mail/` (письма) |
| `users/` | Личный кабинет | `controller` → `GET/PATCH /me`, `/me/subscription`, `/me/history` | `auth/` (кто ты), подписки (что можно) |
| `stores/` | Справочник магазинов | `model/store.py (Store: name/slug/url)` | `parser/` (куда ходить), `products/` (чьи офферы) |
| `categories/` | Полки каталога | `controller` → `GET /categories` | `products/` (фильтр) |
| `products/` + `catalog/` | Товары и склейка | `model/product.py (StoreOffer, OfferPriceHistory)`, `service/matching_service.py` | `stores/`, `search/`, `tracking/` |
| `search/` | Поисковик | `controller/search.py`, `service` (точное→ILIKE→fuzzy), `SearchHistory` | `products/`, `users/` (лимиты по тарифу), `cache/` (кэш 5 мин) |
| `parser/` | Роботы + дирижёр | см. раздел 5 | `stores/`, `products/` (upsert), `cache/` (локи), `worker/` (задачи) |
| `tracking/` | «Следи за ценой» | `service/alert_service.py (scan_for_drops)`, `service/price_refresh.py`, `service/retention.py` | `products/`, `payment/` (advanced-фича), `worker.sync_prices` |
| `payment/` | Касса (ЮKassa, заглушка) | `controller/payment.py`, `service` (trial 10дн, paid 30дн, скидка 20% первый раз) | `users/`, `auth/` |
| `admin/` | Кабинет директора | `controller` → `/admin/users`, `/admin/parsers/run`, `/admin/stats` | Все модули (требует `get_current_admin`) |
| `broadcast/` | Громкоговоритель админа | `service/broadcast_service.py`, задача `send_broadcast` | `users/`, `worker/` |
| `export/` | Принтер (PDF/CSV, advanced) | `controller`, `reportlab` + `fonts-dejavu-core` | `products/`, подписки |
| `feedback/` | Книга жалоб | `controller` | `mail/` |
| `mail/` | Почта | `service` (`console` в деве, `smtp` в проде) | `auth/` (восстановление), `broadcast/` |
| `cache/` | Стикеры Redis | `service/redis_cache.py` | Все (кэш, локи, лимиты) |
| `shared/` | Общие ключи | `deps.py (get_current_user, get_current_admin, require_active_subscription)` | Все контроллеры |
| `middleware/` | Досмотр | `rate_limit.py`, `request_id.py` | `main.py` |

Связи одной строкой: `auth` доказывает кто ты → `shared/deps` проверяет → `users/payment` решают что тебе можно → `search/products` отдают товары → `parser/worker` их обновляют → `tracking` будит если подешевело → `cache` ускоряет → `admin/broadcast/export` управляют.

Проверено: `backend/src/main.py:10-26,65-79`, `backend/src/modules/` (листинг 18 шт), `backend/src/worker.py`, `docs/technical-specification.md:3.2-3.3`.

---

## 8. Фронтенд по косточкам

### `app/` — улицы (Next.js App Router)
Файл `page.tsx` внутри папки = страница. `layout.tsx` = рамка вокруг.

| Путь | Что там |
|---|---|
| `app/layout.tsx` | `<html lang="ru">`, тема (скрипт anti-flash), `<Providers>` (React Query + Effector + тема) |
| `app/page.tsx` | Лендинг: Header + homeWidget + Footer |
| `app/search/` | Поиск + `?q=` |
| `app/product/[id]/` | Карточка товара + история цен |
| `app/login/`, `app/register/`, `app/verify-email/` | Вход, регистрация, подтверждение |
| `app/account/`, `app/subscription/`, `app/tariffs/` | Кабинет, подписка, тарифы |
| `app/admin/` | Админка (за `RequireAdmin`) |
| `app/contacts/`, `app/faq/` | Статика |

Правило `use client`: только если хуки (`useState`, `usePathname`) или браузер (`localStorage`). Остальное — Server Components (быстрее, меньше JS).

### `models/` — склады данных (строго 4 файла!)
Конвенция (`frontend/AGENTS.md`): `schema.ts` (Zod) + `service.ts` (axios) + `hooks.ts` (React Query) + `index.ts` (бочка). Всего 13 сущностей: `auth, user, store, category, product, catalog, search, export, tracking, notification, payment, admin, parser` (см. `models/index.ts`).

Пример (auth, файлы реальные):

- `schema.ts` → `registerRequestSchema = z.object({email: z.string().email(), password: min(6)...})`, типы `RegisterRequest = z.infer<...>` (один источник правды!).
- `service.ts` → `authApi = {register: data => api.post('/auth/register', data), login, refresh, logout, ...}`.
- `hooks.ts` → `useRegister()` (`useMutation`, в `onSuccess` кладёт токены + `setAuth(true)`), `useLogin()`, `useLogout()` (чистит + `queryClient.clear()`), `useUsernameAvailable()` (`useQuery`, включён только если логин подходит под regex).

### `widgets/` — большие витрины
`Header` (client: бургер, `usePathname`, `$isAuth`), `Footer` (server), `homeWidget/` (Hero, Carousel, Advantages, Dashboard, Prices, BannerAccount), `TariffPlans`, `TrackButton` («Следить»), `CatalogExport`, `AccountSidebar`, `RequireAdmin` (403 если не админ), `authorizedHome/`.

### `shared/` — инструменты
`api/axios.ts` (почтальон, см. раздел 9), `config/store.ts` (Effector `$isAuth`), `providers/Providers.tsx` (QueryClient + тема), `lib/utils.ts` (`cn()` = clsx + tailwind-merge), `lib/format.ts`, `ui/*` (shadcn: button, card, input...), `assets/images/*.webp`.

Проверено: `frontend/src/app` (14 записей), `frontend/src/models/{index,auth/*}`, `frontend/src/widgets`, `frontend/src/shared`, `frontend/src/shared/api/axios.ts`, `frontend/src/app/layout.tsx`, `frontend/AGENTS.md`.

---

## 9. Разбор ключевых файлов построчно

### 9.1 `backend/src/main.py` (79 строк) — дверь ресторана
- `1-26 импорты`: FastAPI, CORS, `cors_origins/settings`, `configure_logging`, два middleware, 15 роутеров, `close_redis`, `register_default_parsers`.
- `29-32 lifespan`: при остановке (`yield` после) закрывает Redis (`close_redis`). При старте ничего тяжёлого (парсеры регистрируются ниже, не в lifespan).
- `35 validate_security_settings(settings)`: если `DEBUG=false` а секрет дефолтный — упасть при старте (защита от «забыл сменить»).
- `36 configure_logging(...)`: включает JSON-логи уровня `LOG_LEVEL`.
- `37 register_default_parsers()`: кладёт 4 парсера в `parser_manager` (без этого `/admin/parsers` пуст).
- `39-47 app = FastAPI(...)`: заголовок `BScout API`; если `debug=false` — НЕТ `/docs`, `/redoc`, `/openapi.json` (документацию не светим чужим!).
- `49-63 middleware`: `RequestIdMiddleware` (номерок заказу) → `RateLimitMiddleware` (120/60с) → `CORSMiddleware` (пускать только свои домены, `allow_credentials=True` для кук).
- `65-79 include_router ×15`: health, auth, users, stores, categories, products, search, payment, admin, broadcast, parser, tracking(×2), export, feedback. Порядок не важен (префиксы разные).

### 9.2 `backend/src/config.py` (81 строка) — книга рецептов
- `Settings(BaseSettings)`: каждое поле = переменная окружения. Дефолты локальные (`localhost`, `bscout/bscout`).
- `database_url` (property): склеивает `postgresql+asyncpg://user:pass@host:port/db`. Пароль в URL — нормально для SQLAlchemy, но в логи не печатать!
- `redis_url`: `redis://[:pass@]host:port/0` (база 0).
- JWT: `HS256`, access 15 мин, refresh 30 дней.
- Rate-limit: обычные 120/60с, auth строже 10/300с (от перебора паролей).
- Почта: `mail_backend=console` (в деве письма в лог), SMTP для прода; `smtp_from` с кириллицей.
- `parser_full_sync_enabled=false` — предохранитель ночного обхода.
- `model_config = {env_file: ".env", extra: "ignore"}` — читает `backend/.env`, лишнее молча игнорирует.
- `cors_origins()` — режет строку `"https://a.ru, https://b.ru"` в список.

### 9.3 `backend/src/database.py` (41 строка) — труба к складу
- `NAMING_CONVENTION`: имена индексов `ix_...`, уникальных `uq_...` — чтобы Alembic не генерировал случайные имена.
- `create_async_engine(database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)`: пул 5 постоянных + 10 запасных соединений; `pre_ping` проверяет «ты живой?» перед выдачей.
- `async_session_factory(expire_on_commit=False)`: фабрика сессий; `False` — чтобы объекты не протухали после `commit` (иначе lazy-load вне сессии упадёт).
- `get_db()`: зависимость FastAPI (`Depends(get_db)`): открывает сессию → `yield` (работаем) → `commit` → при исключении `rollback` + `raise`.

### 9.4 `backend/src/celery_app.py` + `worker.py` — будильник и бригады
- `Celery("bscout", broker=redis_url, backend=redis_url)`: и очередь, и результаты — в Redis.
- `beat_schedule`: `sync_catalog 03:00`, `sync_prices 07:30/13:30/19:30`, `expire_subscriptions :05 каждый час`, `cleanup_refresh_tokens 04:30`, `prune_history вс 04:45`. Время UTC!
- `worker.py`: каждая задача — тонкая sync-обёртка `_run_async(async_...)` (свой loop, т.к. Celery синхронный).
- `sync_prices`: `refresh_tracked_offers` (только отслеживаемые, ≤500!) + `AlertService.scan_for_drops` (детектор скидок, его забывали вызывать — баг из MASTERPLAN) + `commit`.
- `expire_subscriptions`: `UPDATE subscriptions SET is_active=false WHERE end_date < now()` (иначе статистика врёт).
- `run_parser`: `parser_service.run_isolated(...)` с `time_limit=6ч` (полный обход не убивать на 5-й минуте!).

### 9.5 `frontend/src/shared/api/axios.ts` (77 строк) — почтальон
- `api = axios.create({baseURL: '/api'})`: относительный путь → работает и локально, и в проде (прокси/ nginx допишет хост).
- `request.use`: если есть `localStorage.access_token` → `Authorization: Bearer ...`.
- `runRefresh`: один полёт на всех (синглтон `refreshInFlight`), `POST /api/auth/refresh {refresh_token}` → кладёт новую пару.
- `response.use`: при `401 && !_retry` → пробует refresh → повторяет исходный запрос с новым токеном → иначе `failAuth()` (чистит storage, `setAuth(false)`, `location='/login'`).
- Подводный камень: токены в `localStorage` (XSS украдёт), зато просто. httpOnly-cookie безопаснее, но сложнее (нужен CSRF).

### 9.6 `docker-compose.yml` (dev, 136 строк) — локальное меню
- `postgres: image 16-alpine, ports ${POSTGRES_HOST_PORT:-5432}:5432, volume pgdata, healthcheck pg_isready, restart unless-stopped`.
- `redis: image 7-alpine, ports ...:6379`.
- `backend: build ./backend, env_file ./backend/.env, depends_on postgres(healthy)+redis, env POSTGRES_HOST=postgres (имя сервиса = DNS!), ports ${BACKEND_PORT:-8000}:8000`.
- `worker: та же сборка, command celery worker --concurrency=1` (1 — вежливо к чужим сайтам + меньше RAM).
- `beat, flower(:5555)` — аналогично. Flower без пароля в деве (`FLOWER_UNAUTHENTICATED_API=true`).

### 9.7 Парсер на примере `tgsm.py` (398 строк)
- Константы (см. раздел 5) → `_clean` (убрать `&nbsp;`, сжать пробелы) → `_safe_price` (обёртка над `parse_price`, `None` вместо исключения) → `_branch_state("3 шт"/"нет")` → `(True/False, qty)`.
- `_session`: переиспользует переданный `httpx.AsyncClient` (тесты!) или создаёт новый с `User-Agent: BScoutBot/0.1`.
- `_fetch`: `safe_request` (ретраи+backoff+timeout) → `response.text` или `None` + запись в `self.errors`.
- `parse_sitemap_urls`: BeautifulSoup `xml` → разделить вложенные sitemap и страницы.
- `collect_product_urls`: BFS-очередь с `visited` и глубиной ≤3 → `filter_product_urls` (только `product_id=`).
- `parse_product_html`: ищет `[itemtype*=Product]` → title (`h1[itemprop=name]`) → price (`meta[itemprop=price]`) → sku (`[itemprop=sku]` или `product_id=` из URL) → stock из `table.filiallist2` по строкам филиалов → breadcrumbs/category/canonical/image/description → `ParseResult(...)`. Чего нет — пишет в `errors` и возвращает `None` (карточка пропускается, весь обход не падает).
- `search`/`update_catalog`/`_parse_many`: семафор + пауза → `asyncio.gather`.

Проверено: `backend/src/main.py`, `config.py`, `database.py`, `celery_app.py`, `worker.py:40-85`, `frontend/src/shared/api/axios.ts`, `docker-compose.yml`, `backend/src/modules/parser/service/parsers/tgsm.py`.

---

## 10. Конфиги и переменные окружения

Правило безопасности: значения — только в gitignored `.env` / `.env.prod`. В репо — только шаблоны. Здесь — только имена и смысл.

### 10.1 Dev (`.env.example`, 6 строк + дефолты compose)

| Переменная | Что значит (по-детски) | Где используется | Дефолт |
|---|---|---|---|
| `BACKEND_PORT` | Дверь бэкенда на твоём ноутбуке | `docker-compose.yml:49`, фронт-прокси | `8000` (локально советуют `8010`, порт занят проектом axidi) |
| `POSTGRES_HOST_PORT` | Дверь базы наружу | `docker-compose.yml:10` | `5432` (локально `5434`) |
| `REDIS_HOST_PORT` | Дверь Redis наружу | `docker-compose.yml:23` | `6379` |
| `JWT_SECRET_KEY` | Печать для паспортов-токенов | `src/config.py:27`, `auth/service/security.py` | `change-me...` (сменить! иначе прод не стартует) |
| `DEBUG` | Режим болтуна | `src/main.py:39` (`true` = есть `/docs`) | `false` |
| `PARSER_FULL_SYNC_ENABLED` | Разрешение на ночной обход | `src/worker.py:57` | `false` |

Внутри compose жёстко зашито (не env): `POSTGRES_DB/USER/PASSWORD=bscout`, `POSTGRES_HOST=postgres`, `REDIS_HOST=redis` (имена сервисов!).

### 10.2 Prod (`.env.prod.example`, 86 строк — главное)

- Домен/TLS: `SERVER_NAME`, `FRONTEND_BASE_URL=https://...`, `TLS_CERT_DIR/_PATH/_KEY_PATH`, `NGINX_*_PORT`, `CLIENT_MAX_BODY_SIZE=2m`.
- Приложение: `APP_NAME`, `IMAGE_TAG`, `DEBUG=false!`, `LOG_LEVEL=INFO`, `CORS_ORIGINS_RAW=https://...`, `UVICORN_WORKERS=2`.
- База: `POSTGRES_DB/USER`, `POSTGRES_PASSWORD` (длинный случайный!), `POSTGRES_MAX_CONNECTIONS=100`, `POSTGRES_SHARED_BUFFERS=256MB`.
- Redis: `REDIS_PASSWORD` (обязателен по примеру, но код его пока не умеет — см. коммент в `docker-compose.prod.yml:102-108`!), `REDIS_MAXMEMORY=256mb`.
- JWT: `JWT_SECRET_KEY` (≥32 случайных, `openssl rand -hex 32`), `JWT_ALGORITHM=HS256`, `ACCESS 15`, `REFRESH 30 дней`.
- Лимиты: `RATE_LIMIT_*`, `AUTH_RATE_LIMIT_*`, `RATE_LIMIT_TRUST_FORWARDED_FOR=true` (только за nginx!), `FORWARDED_ALLOW_IPS=*`.
- Почта: `MAIL_BACKEND=smtp`, `SMTP_HOST/PORT/USER/PASSWORD`, `SMTP_FROM`.
- Деньги: `YOOKASSA_WEBHOOK_SECRET` (пока нет → webhook 503, подпись — заглушка!).
- Соцвход/боты: `VK_*`, `TELEGRAM_BOT_TOKEN/USERNAME` (уведомления, не вход).
- Парсер: `PARSER_FULL_SYNC_ENABLED=false` (включать после проверки!).

Запуск прода: `docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d --build`.

Проверено: `.env.example`, `.env.prod.example`, `backend/src/config.py`, `docker-compose.prod.yml:17-60`.

---

## 11. Запуск локально + проверка + частые ошибки

### 11.1 Быстрый старт (dev)

```bash
# 0. Проверка инструментов
python3 --version  # нужен 3.11
node --version     # нужен 18+
docker --version

# 1. Базы (из корня bscout!)
docker compose up -d
docker compose ps  # postgres + redis healthy

# 2. Бэкенд
cd backend
# venv один на репо (см. AGENTS.md): source ../venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env  # если нет; править только по шаблону!
python -m alembic upgrade head
uvicorn src.main:app --reload --port 8010
# Swagger: http://localhost:8010/docs (только если DEBUG=true в backend/.env)

# 3. Фронт (второе окно терминала)
cd frontend
npm install
npm run dev
# Открыть http://localhost:3000
```

Что должно ответить:

| Сервис | URL | Ожидание |
|---|---|---|
| Фронт | `http://localhost:3000` | Лендинг BScout |
| API | `http://localhost:8010/api/health` | `{"status":"ok",...}` |
| Swagger | `http://localhost:8010/docs` | Список эндпоинтов (DEBUG=true) |
| Flower | `http://localhost:5555` | Очереди Celery |

Полезное:

```bash
cd backend
ruff check src tests && ruff format src tests
python -m pytest tests/unit              # быстрые, без баз
python -m pytest                         # все (нужны postgres+redis+bscout_test)
python -m alembic revision --autogenerate -m "что изменил"  # новая миграция
cd ../frontend
npm run build && npm run lint && npm test
```

### 11.2 Частые ошибки новичка

1. **Порт занят** (`address already in use :8000`) → проект `axidi` сидит на 8000. Лечится `BACKEND_PORT=8010` + `frontend/.env.local: BACKEND_URL=http://localhost:8010`.
2. **`alembic upgrade head` ругается на подключение** → Postgres в Docker не поднят / не тот порт. Проверь `docker compose ps` и `POSTGRES_*` в `backend/.env`.
3. **Фронт `fetch failed /api`** → бэкенд не запущен или прокси смотрит не туда. Проверь `next.config.mjs` + `BACKEND_URL`.
4. **401 на каждом запросе** → протух access (15 мин — нормально!), должен сработать refresh. Если кикает в `/login` — проверь `refresh_token` в localStorage и время на часах.
5. **`parser 0 товаров`** → смотри `errors` в `GET /api/admin/parsers`: таймауты ТГСМ (норма, ретраи), категории Профи в выборке (нужен `section`), sitemap пустой. Полный обход без `PARSER_FULL_SYNC_ENABLED=true` не идёт — так задумано.
6. **Закоммитил `.env`** → так нельзя! Только `.env.example`. Проверь `.gitignore`.
7. **Читаешь ТЗ и не сходится (React 19/CRA)** → ТЗ устарело, верь коду: Next 14 + App Router.

Проверено: `README.md:211-281`, `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md`, `docs/plan/MASTERPLAN.md:96-107`.

---

## 12. Словарь 30 терминов

1. **Frontend (фронтенд)** — витрина: что видит человек. Здесь Next.js.
2. **Backend (бэкенд)** — кухня: готовит данные. Здесь FastAPI.
3. **API** — меню кухни: список блюд-запросов (`GET /api/products`).
4. **HTTP** — язык официанта: «принеси» (GET), «запиши» (POST), «поправь» (PATCH), «убери» (DELETE).
5. **JSON** — записка стандартной формы (`{"price": 4500}`), `snake_case` с обеих сторон.
6. **SSR/CSR** — где собрали страницу: на сервере (быстро для SEO) или в браузере.
7. **App Router** — улицы Next.js: папка = адрес (`app/search/page.tsx` = `/search`).
8. **FSD** — районы витрины: `app` (улицы), `widgets` (дома), `models` (склады), `shared` (инструменты).
9. **Zod** — учитель проверки анкет на фронте.
10. **Pydantic** — тот же учитель, но на бэкенде.
11. **React Query** — дневник фронтенда: помнит ответы, сам обновляет.
12. **Effector** — выключатель «вошёл/вышел» для всего сайта.
13. **JWT** — бумажный браслет на концерте: `access` на 15 мин + `refresh` на 30 дней. Подделать нельзя без печати (`JWT_SECRET_KEY`).
14. **bcrypt** — мясорубка для паролей: обратно не провернуть, только сравнить.
15. **CORS** — список «своих»: браузер не отдаёт ответ чужому сайту.
16. **Middleware** — досмотр на входе (лимиты, номерок запроса).
17. **Rate limit** — «не стучи чаще N раз»: 120/мин обычно, 2/сек на логин, иначе 429.
18. **Postgres** — склад-таблицы на диске.
19. **Redis** — доска-стикеры в памяти: кэш, локи, очередь.
20. **TTL** — время жизни стикера (300 сек = 5 мин).
21. **ORM (SQLAlchemy)** — переводчик «объект <-> строка таблицы».
22. **Миграция (Alembic)** — чертёж перепланировки склада, применяется по порядку.
23. **Docker-образ** — замороженный ланчбокс с приложением.
24. **Контейнер** — разогретый ланчбокс (запущенный образ).
25. **Compose** — меню из нескольких ланчбоксов сразу.
26. **Nginx** — швейцар: TLS, сжатие, лимиты, раздача по `/` и `/api/`.
27. **TLS/HTTPS** — запечатанный конверт (шифрование) + паспорт сайта (сертификат).
28. **Celery/Beat/Flower** — бригада уборщиков + будильник + окошко диспетчера (:5555).
29. **Парсер** — робот-переписчик цен с чужих сайтов (`sitemap.xml` → карточка → `ParseResult`).
30. **Fuzzy-поиск (`pg_trgm`)** — поиск с опечатками («дисплэй» найдёт «дисплей»), только для тарифа Продвинутый.

---

## 13. FAQ: 10 «глупых» вопросов

1. **Где «главная кнопка» проекта?** Две: `backend/src/main.py` (создаёт API) и `frontend/src/app/page.tsx` (главная страница).
2. **Зачем Redis, если есть Postgres?** Postgres — надёжный, но медленный склад. Redis — быстрые стикеры: кэш на 5 мин, локи «парсер уже бежит», очередь задач. Без него каждый поиск считал бы заново, а два парсера дрались бы за один магазин.
3. **Что такое `infra` и `deploy`?** `infra/` — черновики чертежей, `deploy/` + `docker-compose*.yml` — боевые. Удалишь `deploy/nginx/nginx.conf` — прод не поднимется, локалка выживет.
4. **Почему Nginx, а не сразу к бэкенду?** Он держит TLS, режет флуд до Python, сжимает (gzip), отдаёт статику и прячет базы (сеть `data` без выхода наружу).
5. **Почему Celery, а не просто cron?** Обход — 3–4 часа, HTTP столько не живёт (504). Задача кладётся в Redis за 62 мс (202), воркер жуёт её ночью. Плюс Flower показывает очередь.
6. **Где лежат конфиги парсеров?** Вверху `tgsm.py/profi.py/liberti.py/divizion.py` (таймауты, паузы, concurrency) + `parser_service.py` (лимиты, TTL) + env `PARSER_FULL_SYNC_ENABLED`.
7. **Почему ТГСМ такой медленный?** Самый капризный сайт: `TIMEOUT 45с`, `RETRIES 4`, `CONCURRENCY 2`, `DELAY 1с`. Вежливость важнее скорости — иначе забанят.
8. **Что делает каждая строчка? Правда все?** Буквально все — нет (тысячи строк). Правило: каждый ФАЙЛ и каждая КЛЮЧЕВАЯ функция описаны здесь + один сквозной пример + построчный разбор 7 файлов (раздел 9). Этого хватает, чтобы найти любую строчку за минуту.
9. **Почему аналоги не выбрали?** Django — тяжёлый и sync; Flask — собирать всё руками; Mongo — нет связей; SQLite — нет сети; Scrapy/Playwright — тяжело и палевно; K8s — пушка по воробьям; Caddy/Traefik — менее привычны команде.
10. **С чего чинить, если всё упало?** Порядок: `docker compose ps` (базы живы?) → `/api/health` (кухня дышит?) → логи `docker compose logs backend worker` → `/docs` руками повторить запрос → Redis `parser:status:*` (парсер висит?) → Flower (очередь стоит?).

---

## 14. Что учить дальше

1. HTTP + JSON + коды (200/201/401/403/404/422/429) — 1 вечер.
2. Python async/await + FastAPI (Depends, Pydantic) — пиши маленький CRUD.
3. SQL + SQLAlchemy + Alembic — `SELECT/JOIN`, потом `select(User).where(...)`.
4. Docker (образ/слой/том/сеть) — собери свой `Dockerfile`.
5. React + Next App Router (server vs client) — перенеси одну страницу на `useQuery`.
6. Postgres `pg_trgm` + Redis (TTL, NX-локи) — пойми `similarity()` и `acquire_lock`.
7. Парсинг этично: `robots.txt`, паузы, `User-Agent`, sitemap вместо долбёжки.

---

## 15. Выводы, допущения, проверено

### Выводы
- BScout = Next.js-витрина + FastAPI-кухня + Postgres-склад + Redis-стикеры + Celery-уборщики + Nginx-швейцар. Данные — из 4 живых парсеров (ГринСпарк без парсера).
- Критичные предохранители: `PARSER_FULL_SYNC_ENABLED=false`, JWT ≥32, `DEBUG=false` в проде, лимиты на двух уровнях, `migrate` до старта, `client_max_body_size 2m`.
- Главная дыра сейчас (по MASTERPLAN 2026-08-08): мало живых цен (316 живых + 308 демо), деньги принять нельзя (webhook-заглушка), уведомления только in-app.

### Допущения
- Версии из README/package/requirements считаем правдой, если код не противоречит.
- Пустые `infra/docker/Dockerfile.*`, `infra/nginx/nginx.conf`, `deploy/nginx/bscout.conf.template` (файл ожидался, но в репо только `nginx.conf`) — считаем заглушками, не боевыми.
- Детали `matching_service`, `alert_service`, `payment webhook`, `broadcast` — по именам и ТЗ, построчно не разбирались.

### Проверено (прочитано реально)
`README.md`, `DESIGN.md`, `docs/technical-specification.md`, `docs/plan/MASTERPLAN.md:1-239`, `.env.example`, `.env.prod.example`, `docker-compose.yml`, `docker-compose.prod.yml`, `backend/Dockerfile`, `backend/requirements.txt`, `backend/src/main.py`, `config.py`, `database.py`, `celery_app.py`, `worker.py`, `modules/` (листинг), `parser/service/{base,parser_service}.py`, `parser/service/parsers/{__init__,tgsm,profi}.py`, `cache/service/redis_cache.py`, `infra/nginx/{base-nginx.conf,nginx.conf}`, `deploy/nginx/nginx.conf`, `frontend/src/{app,models,widgets,shared}` (листинги), `models/{index,auth/schema,service,hooks}.ts`, `shared/api/axios.ts`, `app/layout.tsx`, `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md`.

### Оставшаяся неопределённость
- [не проверено] Точные тексты `shared/deps.py`, `matching_service.py`, `alert_service.py`, SMTP-доставка, YooKassa-подпись.
- [не проверено] `scripts/ops/*`, `frontend/src/test/*`, `backend/src/cli.py`.
- Расхождения: README trial 10 дней vs ТЗ 7 дней; ТЗ пишет React 19/CRA vs код Next 14; `REDIS_PASSWORD` в прод-примере обязателен, но код его не читает (см. коммент в compose).

> BScout = Next.js 14 + FastAPI + PostgreSQL 16 + Redis 7 + Celery + Nginx + Docker. Сравнивай цены. Экономь время. Выбирай лучшее.
