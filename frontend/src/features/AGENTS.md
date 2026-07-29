# AGENTS.md — features/

Слой **features/** — бизнес-фичи (пользовательские сценарии). Каждая фича — самодостаточный модуль с ui-компонентами, без прямых зависимостей от других фич.

## Структура

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
        ├── SearchBar.tsx          # Поле ввода + кнопка «Найти» (useRouter + useSearchParams)
        └── SearchFilters.tsx      # Сайдбар: магазины, категории, цена, в наличии (useStores, useCategories)
```

## Соглашения

- Каждая фича имеет `index.ts` с реэкспортом публичных компонентов
- UI-компоненты лежат в `ui/`
- Фичи не импортируют друг друга напрямую (только через models/)
- Данные получают через хуки из `models/` (TanStack Query + Effector)
- URL search params — source of truth для параметров поиска
