# AGENTS.md — models/

Слой **models/** — бизнес-сущности: схемы (zod), сервисы (axios), хуки (TanStack Query), стор (Effector).

## Структура

```
models/
├── index.ts                       # Реэкспорт всех моделей
├── auth/                          # Авторизация (Effector-стор)
│   ├── index.ts                   # Реэкспорт: $isAuth, $user, $authPending, useLogin, useRegister, useLogout
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

## Соглашения

- **Модель** = 4 файла: `index.ts`, `schema.ts`, `service.ts`, `hooks.ts` (+ `store.ts` для auth)
- **schema.ts** — zod-схемы для валидации API-ответов и запросов
- **service.ts** — axios-запросы, каждый возвращает сырой Response (без обработки ошибок)
- **hooks.ts** — TanStack Query хуки (`useQuery`/`useMutation`) + инвалидация
- **store.ts** — Effector-стор (только для client state: `$isAuth`, `$user`)
- **TanStack Query** — для server state (данные с API)
- **Effector** — только для client state (авторизация, UI-состояния)
