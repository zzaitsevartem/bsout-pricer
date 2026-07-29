# AGENTS.md — BScout Frontend

Инструкции для AI-агентов, работающих над фронтендом BScout.

## Команды

```bash
npm run dev     # Dev server на :3000
npm run build   # Проверить сборку (0 errors required)
npm run lint    # ESLint
```

## Стек

- Next.js 14 (App Router), React 18, TypeScript 5
- Tailwind CSS v3 — все стили только через utility classes (никаких .css/.scss модулей)
- TanStack Query (server state) + Effector (client state) + Axios
- react-hook-form + @hookform/resolvers/zod (формы)
- FSD (Feature-Sliced Design)

## Структура FSD (послойно)

### `src/app/` — 11 страниц (только композиция)

```
app/
├── layout.tsx              # QueryProvider + AuthGate + globals.css
├── page.tsx                # Главная: Header + HomeWidget + Footer
├── globals.css             # Tailwind directives, CSS-переменные, Google Fonts, btn-* классы
├── login/page.tsx          # Header + LoginForm + соц.кнопки
├── register/page.tsx       # Header + RegisterForm
├── search/page.tsx         # SearchBar + SearchFilters + SearchResults (useSearchParams)
├── product/page.tsx        # Header + ProductDetail + Footer
├── tariffs/page.tsx        # Header + PlanComparison + Footer
├── faq/page.tsx            # Header + заголовок + FaqAccordion + Footer
├── contacts/page.tsx       # Header + ContactInfo + ContactForm + Footer
├── account/page.tsx        # ProtectedRoute → AccountSidebar + AccountProfile
├── subscription/page.tsx   # ProtectedRoute → AccountSidebar + SubscriptionManager
└── admin/page.tsx          # ProtectedRoute → Header(adminBadge) + AdminSidebar + AdminDashboard
```

### `src/features/` — 2 фичи (бизнес-сценарии)

```
features/
├── auth/                          # Аутентификация пользователя
│   ├── index.ts                   # Реэкспорт: LoginForm, RegisterForm, AuthGate
│   └── ui/
│       ├── LoginForm.tsx          # react-hook-form + zod → useLogin → effector $isAuth
│       ├── RegisterForm.tsx       # react-hook-form + zod → useRegister → effector $isAuth
│       └── AuthGate.tsx           # Инициализация: useMe → effector $user
└── search/                        # Поиск товаров
    ├── index.ts                   # Реэкспорт: SearchBar, SearchFilters
    └── ui/
        ├── SearchBar.tsx          # Поле ввода + кнопка «Найти»
        └── SearchFilters.tsx      # Сайдбар: магазины, категории, цена, в наличии
```

### `src/models/` — 10 моделей (данные + бизнес-логика)

```
models/
├── index.ts                       # Реэкспорт всех моделей
├── auth/                          # Effector-стор + хуки авторизации
│   ├── index.ts
│   ├── schema.ts                  # AuthResponse, LoginRequest, RegisterRequest
│   ├── service.ts                 # login(), register(), refresh(), logout()
│   ├── hooks.ts                   # useLogin, useRegister, useLogout
│   └── store.ts                   # $isAuth, $user, $authPending, $token
├── user/                          # Профиль пользователя
│   ├── index.ts
│   ├── schema.ts                  # UserResponse, SubscriptionResponse
│   ├── service.ts                 # getMe(), updateMe(), getSubscription()
│   └── hooks.ts                   # useMe, useUpdateMe, useSubscription
├── product/                       # Товары и поиск
│   ├── index.ts
│   ├── schema.ts                  # ProductResponse, ProductSearchParams, ProductListResponse
│   ├── service.ts                 # search(), getById(), getPriceHistory()
│   └── hooks.ts                   # useProductSearch, useProduct, usePriceHistory
├── store/                         # Магазины
│   ├── index.ts
│   ├── schema.ts                  # StoreResponse, StoreCreateRequest
│   ├── service.ts                 # getAll(), getById(), create(), update()
│   └── hooks.ts                   # useStores, useStore, useCreateStore
├── category/                      # Категории
│   ├── index.ts
│   ├── schema.ts                  # CategoryResponse, CategoryCreateRequest
│   ├── service.ts                 # getAll(), getById(), create(), update()
│   └── hooks.ts                   # useCategories, useCategory
├── plan/                          # Тарифные планы
│   ├── index.ts
│   ├── schema.ts                  # PlanResponse
│   ├── service.ts                 # getAll()
│   └── hooks.ts                   # usePlans
├── search/                        # История поиска
│   ├── index.ts
│   ├── schema.ts                  # SearchHistoryResponse
│   ├── service.ts                 # getHistory()
│   └── hooks.ts                   # useSearchHistory
├── admin/                         # Админ-панель
│   ├── index.ts
│   ├── schema.ts                  # AdminStats, AdminUser
│   ├── service.ts                 # getStats(), getUsers()
│   └── hooks.ts                   # useAdminStats, useAdminUsers
├── payment/                       # Оплата
│   ├── index.ts
│   ├── schema.ts                  # SubscribeRequest
│   ├── service.ts                 # subscribe(), cancel()
│   └── hooks.ts                   # useSubscribe, useCancelSubscription
└── parser/                        # Парсеры (админка)
    ├── index.ts
    ├── schema.ts                  # ParserStatus
    ├── service.ts                 # getParsers(), runParser()
    └── hooks.ts                   # useParsers, useRunParser
```

### `src/widgets/` — 12 виджетов (композиционные блоки)

```
widgets/
├── Header/ui/Header.tsx           # Auth-aware шапка (usePathname, useUnit $isAuth)
├── Footer/ui/Footer.tsx           # Server component
├── homeWidget/ui/                 # Виджет главной страницы
│   ├── index.tsx                  # HomeWidget — композиция Hero + Carousel + ...
│   ├── Hero/Hero.tsx
│   ├── Carousel/Carousel.tsx
│   ├── Advantages/Advantages.tsx
│   ├── Dashboard/Dashboard.tsx    # useProductSearch (live API, auth или статика)
│   ├── Prices/Prices.tsx          # usePlans + useSubscription
│   └── BannerAccount/BannerAccount.tsx
├── AccountSidebar/ui/AccountSidebar.tsx  # Навигация: profile | subscription | history | settings
├── AccountProfile/ui/AccountProfile.tsx  # Профиль: view/edit + тариф + история + недавние
├── PlanComparison/ui/PlanComparison.tsx  # Таблица сравнения тарифов (usePlans)
├── FaqAccordion/ui/FaqAccordion.tsx      # Аккордеон с вопросами
├── ContactWidget/ui/ContactWidget.tsx    # ContactInfo + ContactForm
├── ProductDetail/ui/ProductDetail.tsx    # Детальная товара (заглушка)
├── AdminSidebar/ui/AdminSidebar.tsx      # Навигация админ-панели
├── AdminDashboard/ui/AdminDashboard.tsx  # Дашборд + таблицы пользователей/парсеров (заглушка)
├── SubscriptionManager/ui/SubscriptionManager.tsx  # Управление подпиской (заглушка)
└── SearchResults/ui/SearchResults.tsx    # Список + пагинация + сортировка
```

### `src/shared/` — 4 слоя (инфраструктура)

```
shared/
├── api/
│   └── axios.ts                       # Axios instance + Bearer token + refresh interceptor
├── config/
│   ├── query-client.ts                # TanStack QueryClient config
│   └── store.ts                       # Effector store registration
├── lib/
│   └── utils.ts                       # cn() — conditional Tailwind classes
├── providers/
│   ├── Providers.tsx                   # QueryProvider + AuthGate в layout
│   └── QueryProvider.tsx               # TanStack QueryProvider
├── ui/
│   ├── ProtectedRoute.tsx              # Guard: перенаправление на /login при !isAuth
│   ├── DecorativeLines.tsx             # Декоративные SVG-линии
│   └── IconSVG.tsx                     # Набор SVG-иконок (Logo, Arrow, Check, Social)
└── assets/images/                      # .webp изображения (через import → .src)
    ├── cube.webp, dashboard.webp, helix.webp, ...
    ├── logo1.webp, torus.webp, vurtel.webp, ...
    └── store-лого: taggsm.webp, profi.webp, liberty.webp, greenSpark.webp, divizion.webp
```

## Соглашения по коду

- **"use client"** — только если есть React-хуки (useState, useEffect, usePathname). Все остальные — Server Components
- **Импорты** — через `@/` алиас (`@/features/auth`, `@/widgets/Header/ui/Header`, `@/models/product`)
- **cn()** из `@/lib/utils` для условных Tailwind-классов
- **SVG-иконки** — инлайном в JSX (не вынесены в отдельные файлы)
- **Изображения** — `import img from '@/shared/assets/images/img.webp'`, использовать как `img.src`
- **Анимации** — в tailwind.config.ts (keyframes + animation). Не использовать styled-jsx
- **Цвета/шрифты** — через tailwind.config.ts, не хардкодить значения
- **Адаптивность** — Tailwind breakpoints (max-md, max-lg, lg, etc.)
- **Страницы** — только композиция, никакой логики. Вся логика в виджетах/фичах/моделях
- **Данные** — TanStack Query для server state, Effector для client state ($isAuth, $user)

## Ключевые файлы

- `tailwind.config.ts` — кастомные цвета (slate, ivory, olive, body и др.), шрифты (Raleway, Montserrat), keyframes
- `next.config.mjs` — прокси /api/* → localhost:8000
- `globals.css` — Tailwind directives, CSS variables, Google Fonts, кастомные классы (btn-primary, btn-secondary и др.)
- `lib/utils.ts` — cn() функция

## Дизайн-токены

- Цвета: slate #141413 (текст), ivory #FAF9F5 (фон), olive #788C5D (акцент), green-discount #4A5D2B
- Шрифты: Raleway (основной), Montserrat (капс), DM Sans (второстепенный)
- Кнопки: btn-primary, btn-secondary, btn-ghost, btn-danger, btn-sm, btn-arrow
- Формы: bg-ivory, border-border-default, focus:border-slate

## После изменений

Всегда запускать `npm run build && npm run lint` перед завершением работы.
