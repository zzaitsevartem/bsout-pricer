# Review: Frontend-Backend Models (Zod + Types + Axios + React Query)

**Дата:** 2026-07-14  
**Статус:** Завершено

---

## Архитектура

Цепочка для каждого эндпоинта:

```
Zod schema → TypeScript type → Axios service → React Query hook
```

```
src/
├── shared/api/axios.ts          # Единый axios инстанс + interceptors
└── models/
    ├── index.ts                 # Barrel export всех модулей
    ├── auth/
    │   ├── schema.ts            # Zod схемы + типы
    │   ├── service.ts           # Axios запросы
    │   ├── hooks.ts             # React Query хуки
    │   └── index.ts             # Barrel export
    ├── user/
    ├── store/
    ├── category/
    ├── product/
    ├── search/
    ├── payment/
    ├── admin/
    └── parser/
```

---

## Модули

### 1. Shared Axios (`src/shared/api/axios.ts`)
- Базовый URL: `/api`
- **Request interceptor** — подставляет `Authorization: Bearer <token>` из localStorage
- **Response interceptor** — автоматический рефреш при 401, редирект на `/login` при неудаче

### 2. Auth (`src/models/auth/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `POST /auth/register` | `useRegister()` | Регистрация |
| `POST /auth/login` | `useLogin()` | Логин + сохранение токенов |
| `POST /auth/refresh` | — | Рефреш (через interceptor) |
| `POST /auth/logout` | `useLogout()` | Выход + очистка |

### 3. User (`src/models/user/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `GET /users/me` | `useMe()` | Текущий пользователь |
| `PATCH /users/me` | `useUpdateMe()` | Обновление профиля |
| `GET /users/me/subscription` | `useSubscription()` | Активная подписка |
| `POST /users/me/subscription` | `useCreateSubscription()` | Создание подписки |

### 4. Store (`src/models/store/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `GET /stores` | `useStores()` | Список магазинов |
| `GET /stores/:id` | `useStore(id)` | Магазин по ID |
| `POST /stores` | `useCreateStore()` | Создание (admin) |
| `PATCH /stores/:id` | `useUpdateStore()` | Обновление (admin) |

### 5. Category (`src/models/category/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `GET /categories` | `useCategories()` | Список категорий |
| `GET /categories/:id` | `useCategory(id)` | Категория по ID |
| `POST /categories` | `useCreateCategory()` | Создание (admin) |
| `PATCH /categories/:id` | `useUpdateCategory()` | Обновление (admin) |

### 6. Product (`src/models/product/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `GET /products` | `useProductSearch(params)` | Поиск с фильтрами |
| `GET /products/:id` | `useProduct(id)` | Товар по ID |
| `GET /products/:id/price-history` | `usePriceHistory(id)` | История цен |

### 7. Search (`src/models/search/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `GET /search/history` | `useSearchHistory()` | История поиска |

### 8. Payment (`src/models/payment/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `POST /payment/subscribe` | `useSubscribe()` | Оплата подписки |
| `POST /payment/cancel` | `useCancelSubscription()` | Отмена подписки |

### 9. Admin (`src/models/admin/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `GET /admin/stats` | `useAdminStats()` | Статистика |
| `GET /admin/users` | `useAdminUsers(skip, limit)` | Список пользователей |
| `GET /admin/users/:id` | `useAdminUser(id)` | Пользователь по ID |
| `POST /admin/users/:id/toggle-active` | `useToggleUserActive()` | Блокировка |

### 10. Parser (`src/models/parser/`)
| Endpoint | Хук | Описание |
|----------|-----|----------|
| `GET /admin/parsers` | `useParsers()` | Список парсеров |
| `POST /admin/parsers/run` | `useRunParser()` | Запуск парсера |

---

## Использование

```tsx
import { useProductSearch, type ProductSearchParams } from '@/models/product';

function SearchPage() {
  const params: ProductSearchParams = { q: 'дисплей iphone', page: 1, per_page: 20 };
  const { data, isLoading } = useProductSearch(params);

  if (isLoading) return <Spinner />;
  return data?.results.map(p => <ProductCard key={p.id} product={p} />);
}
```
