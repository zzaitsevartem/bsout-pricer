# AGENTS.md — src/

Корень исходного кода фронтенда. Сборка 5 слоёв FSD (Feature-Sliced Design).

## Слои

```
src/
├── app/          # 11 страниц — только композиция виджетов
├── features/     # 2 бизнес-фичи — auth, search
├── models/       # 10 моделей — schema, service, hooks, store
├── widgets/      # 12 композиционных блоков
└── shared/       # Инфраструктура — api, config, lib, providers, ui, assets
```

## Правила зависимостей (FSD)

```
app → widgets → features → models → shared
  └──────────── features ────────┘
         (features могут импортировать models напрямую)
```

- `app/` импортирует `widgets/`, `features/`, `shared/`
- `widgets/` импортирует `features/`, `models/`, `shared/`
- `features/` импортирует `models/`, `shared/`
- `models/` импортирует только `shared/` (api, config)
- `shared/` не импортирует ничего из проекта (только библиотеки)

## Быстрый старт

```bash
npm run dev     # Dev server на :3000
npm run build   # Проверить сборку (0 errors required)
npm run lint    # ESLint
```

## Ключевые технологии

- **Next.js 14** — App Router, Server Components
- **Tailwind CSS v3** — все стили через utility classes
- **TanStack Query** — server state (данные с API)
- **Effector** — client state (авторизация)
- **Axios** — HTTP-клиент с Bearer + refresh interceptor
- **react-hook-form + zod** — формы и валидация
