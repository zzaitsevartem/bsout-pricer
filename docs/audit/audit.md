# Аудит проекта BScout

Дата: 2026-07-29 (обновлено, FSD-рефакторинг + /search integration)

---

## 1. Общее состояние

| Компонент | Статус |
|-----------|--------|
| Backend (FastAPI) | 11 модулей, 30 эндпоинтов, 8 SQLAlchemy моделей (+ Plan) |
| Frontend (Next.js 14) | 11 страниц, FSD-структура, effector + TanStack Query |
| Docker (PostgreSQL + Redis) | ✅ **Запущен** (bscout-postgres + bscout-redis) |
| Alembic | ✅ 2 миграции применены к живой БД |
| Seed data | ✅ 2 пользователя, 5 магазинов, 5 категорий, 10 товаров, 60 записей истории цен |
| Backend tests | ✅ **19/19 тестов проходят** (pytest + SQLite + mock Redis) |
| Интеграция фронта и бэка | Auth (login/register) — готово, Header — auth-aware, Dashboard — живые товары, Prices — планы с бэка |
| Парсеры | BaseParser ABC + ParserManager, реальных парсеров нет |

---

## 2. Backend — полный список эндпоинтов

### Публичные (7)
| Метод | Путь | Доступ |
|-------|------|--------|
| GET | /api/health | Public |
| POST | /api/auth/register | Public |
| POST | /api/auth/login | Public |
| POST | /api/auth/refresh | Public |
| GET | /api/stores | Public |
| GET | /api/categories | Public |
| GET | /api/plans | Public |

### Требуют аутентификации (11)
| Метод | Путь | Описание |
|-------|------|----------|
| POST | /api/auth/logout | Выход (требует Bearer) |
| GET | /api/users/me | Профиль текущего пользователя |
| PATCH | /api/users/me | Обновление профиля |
| GET | /api/users/me/subscription | Текущая подписка |
| POST | /api/users/me/subscription | Создание подписки |
| GET | /api/products | Поиск товаров (q, store, category, price range, sort, pagination) |
| GET | /api/products/{id} | Детальная товара |
| GET | /api/products/{id}/price-history | История цен |
| GET | /api/search/history | История поиска пользователя |
| POST | /api/payment/subscribe | Оплата подписки |
| POST | /api/payment/cancel | Отмена подписки |

### Требуют прав администратора (12)
| Метод | Путь |
|-------|------|
| POST | /api/stores | Создание магазина |
| PATCH | /api/stores/{id} | Обновление магазина |
| GET | /api/stores/{id} | Детальная магазина |
| POST | /api/categories | Создание категории |
| PATCH | /api/categories/{id} | Обновление категории |
| GET | /api/categories/{id} | Детальная категории |
| GET | /api/admin/stats | Статистика дашборда |
| GET | /api/admin/users | Список пользователей |
| GET | /api/admin/users/{id} | Пользователь по ID |
| POST | /api/admin/users/{id}/toggle-active | Блокировка/разблокировка |
| GET | /api/admin/parsers | Статус парсеров |
| POST | /api/admin/parsers/run | Запуск парсера |

---

## 3. Frontend — постраничный аудит интеграции

### 3.1 Статус API-интеграции

| Роут | Страница | Backend API | Интеграция | Data source |
|------|----------|-------------|------------|-------------|
| `/` | Главная (Dashboard) | `GET /api/products?per_page=4` | ✅ **Готова** | useProductSearch (auth → живые товары, иначе статика) |
| `/` | Главная (Prices) | `GET /api/plans` + `GET /me/subscription` | ✅ **Готова** | usePlans + useSubscription |
| `/login` | Вход | `POST /api/auth/login` | ✅ **Готова** | React Hook Form + zod + useLogin |
| `/register` | Регистрация | `POST /api/auth/register` | ✅ **Готова** | React Hook Form + zod + useRegister |
| `/tariffs` | Тарифы | `GET /api/plans` + `GET /me/subscription` | ✅ **Готова** | usePlans + useSubscription |
| `/search` | Поиск | `GET /api/products` | ✅ **Готова** | useProductSearch (URL params, фильтры, пагинация, сортировка) |
| `/product` | Детальная | `GET /api/products/{id}`, `/price-history` | ❌ Mock | Жёстко зашитые данные |
| `/faq` | FAQ | — (лендинг) | ✅ Не требует API | Статика |
| `/contacts` | Контакты | — | ❌ Форма не отправляет | Статика |
| `/account` | Профиль | `GET /api/users/me`, `PATCH /api/users/me` | ✅ **Готова** | useMe + useUpdateMe + react-hook-form |
| `/subscription` | Подписка | `GET /me/subscription`, `POST /api/payment/*` | ❌ Mock | Жёстко зашитые данные |
| `/admin` | Админка | `GET /api/admin/*`, `GET /api/admin/parsers` | ❌ Mock | Жёстко зашитые данные |

### 3.2 Структура FSD

```
src/
├── app/                        # 11 страниц (App Router) — тонкая композиция
│   ├── layout.tsx              # Providers (QueryProvider + AuthGate)
│   ├── page.tsx                # 13 строк: Header + HomeWidget + Footer
│   ├── login/page.tsx          # 40 строк: Header + LoginForm + Footer
│   ├── register/page.tsx       # 25 строк: Header + RegisterForm + Footer
│   ├── search/page.tsx         # 188 строк: useSearchParams → SearchBar + SearchFilters + SearchResults
│   ├── product/page.tsx        # 9 строк: Header + ProductDetail + Footer
│   ├── tariffs/page.tsx        # 25 строк: Header + PlanComparison + Footer
│   ├── faq/page.tsx            # 24 строки: Header + FaqAccordion + Footer
│   ├── contacts/page.tsx       # 26 строк: Header + ContactInfo + ContactForm + Footer
│   ├── account/page.tsx        # 24 строки: ProtectedRoute + Header + AccountSidebar + AccountProfile + Footer
│   ├── subscription/page.tsx   # 25 строк: ProtectedRoute + Header + AccountSidebar + SubscriptionManager + Footer
│   └── admin/page.tsx          # 17 строк: ProtectedRoute + Header + AdminSidebar + AdminDashboard
├── features/
│   ├── auth/                   # Auth feature
│   │   ├── index.ts
│   │   └── ui/
│   │       ├── LoginForm.tsx   # react-hook-form + zod → useLogin → effector
│   │       ├── RegisterForm.tsx # react-hook-form + zod → useRegister → effector
│   │       └── AuthGate.tsx    # Инициализация: useMe → effector $user
│   └── search/                 # Search feature
│       ├── index.ts
│       └── ui/
│           ├── SearchBar.tsx   # Строка поиска (input + кнопка)
│           └── SearchFilters.tsx # Сайдбар с фильтрами (store, category, price, in_stock)
├── models/                     # TanStack Query hooks + service + effector store
│   ├── auth/                   # login/register/logout hooks + store ($isAuth, $user)
│   ├── user/                   # useMe, useUpdateMe, useSubscription
│   ├── product/                # useProductSearch, useProduct, usePriceHistory
│   ├── search/                 # useSearchHistory
│   ├── store/                  # useStores, useStore
│   ├── category/               # useCategories, useCategory
│   ├── plan/                   # usePlans (GET /api/plans)
│   ├── admin/                  # useAdminStats, useAdminUsers
│   ├── payment/                # useSubscribe, useCancelSubscription
│   └── parser/                 # useParsers, useRunParser
├── widgets/                    # 12 композиционных блоков
│   ├── Header/                 # Auth-aware: $isAuth → профиль/выход или вход/регистрация
│   ├── Footer/                 # Server component
│   ├── homeWidget/             # Hero, Carousel, Advantages, Dashboard, Prices, Banner
│   ├── AccountSidebar/         # Навигация аккаунта (profile/subscription/history/settings)
│   ├── AccountProfile/         # Профиль: view/edit, тариф, история поиска, недавние
│   ├── PlanComparison/         # Таблица сравнения тарифов
│   ├── FaqAccordion/           # Аккордеон FAQ
│   ├── ContactWidget/          # Контакты (ContactInfo + ContactForm)
│   ├── ProductDetail/          # Детальная товара (заглушка)
│   ├── AdminSidebar/           # Навигация админки
│   ├── AdminDashboard/         # Дашборд админки (статистика, таблицы)
│   ├── SubscriptionManager/    # Управление подпиской (текущий тариф, смена, оплата, отмена)
│   └── SearchResults/          # Результаты поиска + пагинация + сортировка
└── shared/
    ├── api/axios.ts            # Axios instance + Bearer + refresh interceptor
    ├── lib/utils.ts            # cn()
    ├── providers/              # QueryProvider + AuthGate
    └── ui/ProtectedRoute.tsx   # Guard для авторизованных страниц
```

---

## 4. Что НЕ реализовано / требует доработки

### 4.1 Auth — готово
- [x] LoginForm с react-hook-form + zod — отправляет `POST /api/auth/login`
- [x] RegisterForm — отправляет `POST /api/auth/register`
- [x] AuthGate — инициализация через `GET /api/users/me`
- [x] Header — динамический (профиль если auth, вход/регистрация если нет)
- [x] Axios interceptor — Bearer + refresh token при 401
- [x] Effector store — `$isAuth`, `$user`, `$authPending`
- [x] Logout — очистка localStorage + сброс стора
- [x] **ProtectedRoute** — guard для /account, /subscription, /admin
- [x] **Account page** — useMe + useUpdateMe + react-hook-form редактирование
- [ ] **Redirect на /login при 401** — пока не реализован (кроме axios interceptor)

### 4.2 Поиск (/search) — ✅ готово
- [x] Поле поиска связано с `GET /api/products?q=...` через URL search params
- [x] Фильтры (store, category, price range) — передаются как query params, URL shareable
- [x] Пагинация — связана с `page` и `per_page`, URL-driven
- [x] Сортировка — `sort_by` в URL (price_asc, price_desc, date)
- [x] `is_cheapest` — отображается из ответа API
- [x] Loading state — «Загрузка результатов...»
- [x] Empty state — «Ничего не найдено»
- [x] Error state — «Ошибка загрузки» + кнопка повтора
- [x] FSD: SearchBar + SearchFilters (features/search/), SearchResults (widgets/SearchResults/)

### 4.3 Детальная товара (/product)
- [ ] Принимать `product_id` из query params
- [ ] Загружать `GET /api/products/{id}`
- [ ] Отображать список предложений магазинов
- [ ] История цен — `GET /api/products/{id}/price-history`
- [ ] Кнопка «Перейти в магазин» — ссылка на `product_url`

### 4.4 Профиль (/account)
- [x] Загружать реальные данные через `useMe()`
- [x] Форма редактирования — `PATCH /api/users/me` (react-hook-form + zod)
- [ ] История поиска — `GET /api/search/history`
- [ ] Недавно просмотренные — пока нет бэка (нужна отдельная модель)
- [ ] Саб-роуты (/account/history, /account/settings) — не существуют

### 4.5 Подписка (/subscription)
- [ ] Отображать реальную подписку — `GET /api/users/me/subscription`
- [ ] Кнопки смены тарифа — `POST /api/payment/subscribe`
- [ ] Отмена подписки — `POST /api/payment/cancel`
- [ ] Способ оплаты — заглушка (нет бэка)

### 4.6 Админка (/admin)
- [ ] Статистика дашборда — `GET /api/admin/stats`
- [ ] Список пользователей — `GET /api/admin/users`
- [ ] Парсеры — `GET /api/admin/parsers`, `POST /api/admin/parsers/run`

### 4.7 Технический долг
- [x] **SubscriptionGuard на бэке** — прикручен к products/search/price-history
- [x] **Logout на бэке** — пишет refresh в Redis blacklist с TTL
- [x] **Seed данные** — stores, categories, admin user, тестовые продукты (✅)
- [ ] **Guard для тарифов** — Пробный (10 товаров), Базовый (100), Продвинутый (безлимит)
- [ ] **shadcn/ui** — не установлен (только Radix примитивы в package.json)
- [ ] **404 страница** — не кастомная
- [ ] **Loading states** — нет skeleton/spinner на загружаемых страницах
- [ ] **error.tsx** — нет глобальной обработки ошибок

---

## 5. Backend — что требует доработки

| # | Задача | Статус |
|---|--------|--------|
| 1 | **Docker** — запустить PostgreSQL + Redis | ✅ **Запущен** |
| 2 | **Alembic миграции** — применить `alembic upgrade head` | ✅ Применены |
| 3 | **Plan model** — таблица планов с seed (trial/basic/advanced) | ✅ Миграция + seed |
| 4 | **Logout** — запись refresh в Redis blacklist | ✅ Реализован |
| 5 | **SubscriptionGuard** — прикрутить к products/search | ✅ Прикручен |
| 6 | **Seed scripts** — stores, categories, admin user, тестовые продукты | ✅ **Созданы** |
| 7 | **PATCH /users/me** — MissingGreenlet fix (db.refresh) | ✅ **Починено** |
| 8 | **Fuzzy search** — pg_trgm для продвинутого тарифа | ❌ |
| 9 | **Реальные парсеры** — TGSM, Profi, Liberty, GreenSpark, Divizion | ❌ |
| 10 | **Pagination helper** — вынести в shared | ❌ |
| 11 | **Error handling** — глобальный exception handler | ❌ |
| 12 | **Search history сохранение** — триггерить при поиске | ❌ |

---

## 6. Сводка

```
Backend endpoints:     30/30 = 100% (реализовано)
Alembic:               ✅ 2 миграции применены
Backend tests:         19/19 = 100% (pytest)
Frontend build:        ✅ 0 ошибок (pnpm build)
Frontend pages:        11/11 = 100% (FSD-композиция, тонкие page.tsx)
API integration:       7/11 = 64% (login + register + tariffs + Dashboard + Prices + Account + Search)
  ├── /                ✅ Dashboard (useProductSearch) + Prices (usePlans)
  ├── /login           ✅ 100%
  ├── /register        ✅ 100%
  ├── /tariffs         ✅ 100% (usePlans + useSubscription)
  ├── /account         ✅ 100% (useMe + useUpdateMe + react-hook-form)
  ├── /search          ✅ 100% (useProductSearch, URL-params, filters, pagination, sort)
  ├── /product         ❌ 0% (заглушка)
  ├── /subscription    ❌ 0% (заглушка)
  ├── /admin           ❌ 0% (заглушка)
  ├── /contacts        ❌ 0% (форма не отправляет)
  └── /faq             ✅ не требует API
Auth system:           ✅ 95% (логин/регистрация/logout/Header/профиль — готово)
Docker:                ✅ Запущен (bscout-postgres + bscout-redis)
Backend server:        ✅ Запущен на :8000
Seed data:             ✅ 2 user, 5 stores, 5 categories, 10 products, 60 price history
Parsers:               0/5 = 0%
```

---

## 7. Рекомендуемый следующий шаг

### Интеграция страниц фронта с API

1. ✅ **Поиск** `/search` → `GET /api/products` — **готово**
2. **Интегрировать детальную товара** `/product` → `GET /api/products/{id}` + `/price-history`
3. **Интегрировать подписку** `/subscription` → живая подписка + POST /api/payment/*
4. **Интегрировать админку** `/admin` → `GET /api/admin/*`

### Технические улучшения

5. **Fuzzy search (pg_trgm)** — для продвинутого тарифа
6. **Реальные парсеры** — TGSM, Profi, Liberty, GreenSpark, Divizion
7. **Глобальный error handling** — exception handler в main.py
8. **Проверить работает ли frontend против живого бэка** (запустить оба и пройти сценарии)
