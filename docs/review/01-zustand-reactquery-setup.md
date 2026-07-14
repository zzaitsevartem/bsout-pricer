# Review: Настройка Effector (стор) + React Query (запросы)

**Дата:** 2026-07-14  
**Статус:** Завершено

---

## Что сделано

### 1. Зависимости

- **effector** `^23.4.4` + **effector-react** `^23.3.0` — уже были в проекте, используются как основной state manager
- **lucide-react** — исправлена версия с `^18.0.0` на `^1.24.0` (18.x не существует)

### 2. FSD-структура для state management

```
src/shared/
├── lib/
│   └── utils.ts              # cn() — Tailwind class merge (clsx + tailwind-merge)
├── config/
│   ├── query-client.ts       # Конфигурация React Query (QueryClient)
│   └── store.ts              # Effector stores, events, effects
└── providers/
    ├── Providers.tsx         # Корневой провайдер (обёртка)
    └── QueryProvider.tsx     # React Query провайдер ("use client")
```

### 3. Детали файлов

#### `shared/lib/utils.ts`
- Экспорт функции `cn()` — объединяет `clsx` и `twMerge`
- Используется везде для условных Tailwind-классов

#### `shared/config/query-client.ts`
- `makeQueryClient()` — создаёт `QueryClient` с дефолтными настройками
  - `staleTime: 60s` — данные считаются свежими 60 секунд
  - `refetchOnWindowFocus: false` — без рефетча при переключении вкладок
- `getQueryClient()` — SSR-safe (создаёт отдельный клиент на сервере, переиспользует на клиенте)

#### `shared/config/store.ts`
Effector-стор с типизированными сторами, событиями и эффектами:

- **События:** `setAuth`, `setUser`, `reset`
- **Сторы:** `$isAuth` (boolean), `$user` (User | null)

#### `shared/providers/Providers.tsx`
- `"use client"` — нужен для провайдеров
- Обёртка: `Providers` → `QueryProvider` → `children`

#### `shared/providers/QueryProvider.tsx`
- `"use client"`
- Использует `getQueryClient()` для получения/создания клиента
- Оборачивает `children` в `QueryClientProvider`

### 4. Изменение layout.tsx

- Импортирован `Providers` из `@/shared/providers/Providers`
- `{children}` обёрнуто в `<Providers>`

---

## Использование

### Effector

```tsx
import { useUnit } from 'effector-react';
import { $isAuth, $user, setUser } from '@/shared/config/store';

function Profile() {
  const [isAuth, user, setUserHandler] = useUnit([$isAuth, $user, setUser]);

  // ...
}
```

### React Query

```tsx
'use client';

import { useQuery } from '@tanstack/react-query';

function MyComponent() {
  const { data, isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: () => fetch('/api/products').then(r => r.json()),
  });

  // ...
}
```

### cn() утилита

```tsx
import { cn } from '@/shared/lib/utils';

<div className={cn('base-class', isActive && 'active-class', className)} />
```
