# Аудит проекта BScout

Дата: 2026-07-29

---

## 1. Общее состояние

| Компонент | Статус |
|-----------|--------|
| Backend (FastAPI) | 11 модулей, 30 эндпоинтов, 8 SQLAlchemy моделей (+ Plan) |
| Frontend (Next.js 14) | 11 страниц, FSD-структура, effector + TanStack Query |
| Docker (PostgreSQL + Redis) | docker-compose.yml в корне проекта |
| Alembic | Настроен, 2 миграции (init + plans table с seed) |
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
| `/search` | Поиск | `GET /api/products` | ❌ Mock | Жёстко зашитые 5 товаров |
| `/product` | Детальная | `GET /api/products/{id}`, `/price-history` | ❌ Mock | Жёстко зашитые данные |
| `/faq` | FAQ | — (лендинг) | ✅ Не требует API | Статика |
| `/contacts` | Контакты | — | ❌ Форма не отправляет | Статика |
| `/account` | Профиль | `GET /api/users/me`, `PATCH /api/users/me` | ❌ Mock | Жёстко зашитые данные |
| `/subscription` | Подписка | `GET /me/subscription`, `POST /api/payment/*` | ❌ Mock | Жёстко зашитые данные |
| `/admin` | Админка | `GET /api/admin/*`, `GET /api/admin/parsers` | ❌ Mock | Жёстко зашитые данные |

### 3.2 Структура FSD

```
src/
├── app/                        # 11 страниц (App Router)
│   ├── layout.tsx              # Providers (QueryProvider + AuthGate)
│   ├── page.tsx                # Главная — Dashboard (useProductSearch) + Prices (usePlans)
│   ├── login/page.tsx          # LoginForm
│   ├── register/page.tsx       # RegisterForm
│   ├── search/page.tsx         # Mock-данные
│   ├── product/page.tsx        # Mock-данные
│   ├── tariffs/page.tsx        # usePlans + useSubscription
│   ├── faq/page.tsx            # Статика (accordion)
│   ├── contacts/page.tsx       # Статика
│   ├── account/page.tsx        # Mock-данные
│   ├── subscription/page.tsx   # Mock-данные
│   └── admin/page.tsx          # Mock-данные
├── features/
│   └── auth/                   # Auth feature
│       ├── index.ts
│       └── ui/
│           ├── LoginForm.tsx   # react-hook-form + zod → useLogin → effector
│           ├── RegisterForm.tsx # react-hook-form + zod → useRegister → effector
│           └── AuthGate.tsx    # Инициализация: useMe → effector $user
├── models/                     # TanStack Query hooks + service + effector store
│   ├── auth/                   # login/register/logout hooks + store ($isAuth, $user)
│   ├── user/                   # useMe, useUpdateMe, useSubscription
│   ├── product/                # useProducts, useProduct
│   ├── search/                 # useSearchHistory
│   ├── store/                  # useStores, useStore
│   ├── category/               # useCategories, useCategory
│   ├── plan/                   # usePlans (GET /api/plans)
│   ├── admin/                  # useAdminStats, useAdminUsers
│   ├── payment/                # useSubscribe, useCancelSubscription
│   └── parser/                 # useParsers, useRunParser
├── widgets/
│   ├── Header/                 # Auth-aware: $isAuth → профиль/выход или вход/регистрация
│   ├── Footer/                 # Server component
│   └── homeWidget/             # Hero, Carousel, Advantages, Dashboard, Prices, Banner
└── shared/
    ├── api/axios.ts            # Axios instance + Bearer + refresh interceptor
    ├── lib/utils.ts            # cn()
    └── providers/              # QueryProvider + AuthGate
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
- [ ] **Redirect на /login при 401** — пока не реализован (кроме axios interceptor)
- [ ] **Защита роутов** — /account, /subscription, /admin должны редиректить без токена

### 4.2 Поиск (/search) — следующая очередь
- [ ] Связать поле поиска с `GET /api/products?q=...`
- [ ] Фильтры (store, category, price range) — передавать как query params
- [ ] Пагинация — связать с `page` и `per_page`
- [ ] Сортировка — связать с `sort_by`
- [ ] Отображение `is_cheapest` из ответа API
- [ ] Loading state (skeleton)
- [ ] Empty state («Ничего не найдено»)

### 4.3 Детальная товара (/product)
- [ ] Принимать `product_id` из query params
- [ ] Загружать `GET /api/products/{id}`
- [ ] Отображать список предложений магазинов
- [ ] История цен — `GET /api/products/{id}/price-history`
- [ ] Кнопка «Перейти в магазин» — ссылка на `product_url`

### 4.4 Профиль (/account)
- [ ] Загружать реальные данные через `useMe()`
- [ ] Форма редактирования — `PATCH /api/users/me`
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
- [ ] **SubscriptionGuard на бэке** — не прикручен к роутам продуктов
- [ ] **Logout на бэке** — не пишет refresh в Redis blacklist
- [ ] **Guard для тарифов** — Пробный (10 товаров), Базовый (100), Продвинутый (безлимит)
- [ ] **Seed данные** — stores, categories, admin user, тестовые продукты
- [ ] **shadcn/ui** — не установлен (только Radix примитивы в package.json)
- [ ] **404 страница** — не кастомная
- [ ] **Loading states** — нет skeleton/spinner на загружаемых страницах
- [ ] **error.tsx** — нет глобальной обработки ошибок

---

## 5. Backend — что требует доработки

| # | Задача | Статус |
|---|--------|--------|
| 1 | **Docker** — запустить PostgreSQL + Redis | ❌ Не запущен |
| 2 | **Alembic миграции** — применить `alembic upgrade head` | ✅ 2 миграции готовы, не применены |
| 3 | **Plan model** — таблица планов с seed (trial/basic/advanced) | ✅ Миграция + seed |
| 4 | **Logout** — запись refresh в Redis blacklist | ❌ |
| 5 | **SubscriptionGuard** — прикрутить к products/search | ❌ |
| 6 | **Fuzzy search** — pg_trgm для продвинутого тарифа | ❌ |
| 7 | **Реальные парсеры** — TGSM, Profi, Liberty, GreenSpark, Divizion | ❌ |
| 8 | **Seed scripts** — stores, categories, admin user, тестовые продукты | ❌ |
| 9 | **Pagination helper** — вынести в shared | ❌ |
| 10 | **Error handling** — глобальный exception handler | ❌ |
| 11 | **Search history сохранение** — триггерить при поиске | ❌ |

---

## 6. Сводка

```
Backend endpoints:     30/30 = 100% (реализовано)
Alembic:               подготовлен, 2 миграции готовы
Frontend pages:        11/11 = 100% (вёрстка)
API integration:       5/11 = 45% (login + register + tariffs + Dashboard + Prices)
  ├── /                ✅ Dashboard (useProductSearch) + Prices (usePlans)
  ├── /login           ✅ 100%
  ├── /register        ✅ 100%
  ├── /tariffs         ✅ 100% (usePlans + useSubscription)
  ├── /search          ❌ 0%
  ├── /product         ❌ 0%
  ├── /account         ❌ 0%
  ├── /subscription    ❌ 0%
  ├── /admin           ❌ 0%
  ├── /contacts        ❌ 0% (форма не отправляет)
  └── /faq             ✅ не требует API
Auth system:           ✅ 90% (логин/регистрация/logout/Header — готово)
Docker:                ❌ Не запущен (PG + Redis + бэк не запущены)
Parsers:               0/5 = 0%
```

---

## 7. Рекомендуемый следующий шаг

1. **Запустить Docker** → `docker compose up -d`
2. **Применить миграции** → `alembic upgrade head`
3. **Запустить бэк** → `uvicorn src.main:app --reload`
4. **Создать seed data** → stores, categories, admin пользователь
5. **Интегрировать поиск** `/search` → `GET /api/products`
