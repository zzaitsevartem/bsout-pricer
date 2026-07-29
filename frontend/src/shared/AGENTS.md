# AGENTS.md — shared/

Слой **shared/** — инфраструктура: API-клиент, UI-кит, изображения, конфиги. Никакой бизнес-логики.

## Структура

```
shared/
├── api/
│   └── axios.ts                       # Axios instance + Bearer token + refresh interceptor
├── config/
│   ├── query-client.ts                # TanStack QueryClient config
│   └── store.ts                       # Effector store registration
├── lib/
│   └── utils.ts                       # cn() — conditional Tailwind classes (clsx + twMerge)
├── providers/
│   ├── Providers.tsx                   # QueryProvider + AuthGate (для layout.tsx)
│   └── QueryProvider.tsx               # TanStack QueryProvider (HydrationBoundary)
├── ui/
│   ├── ProtectedRoute.tsx              # Guard: /login redirect при !isAuth
│   ├── DecorativeLines.tsx             # Декоративные SVG-линии (Hero, разделы)
│   └── IconSVG.tsx                     # SVG-иконки: Logo, ArrowRight, Check, Social (VK, TG, YouTube)
└── assets/images/                      # .webp изображения (import → .src)
    ├── cube.webp                       # Декоративный куб
    ├── dashboard.webp                  # Скриншот дашборда
    ├── helix.webp, helixTwo.webp       # Спирали
    ├── torus.webp, figure*.webp        # Геометрические фигуры
    ├── logo1.webp                      # Логотип
    ├── vurtel.webp                     # Вюртель
    ├── emojiStar.webp                  # Звезда-эмодзи
    └── store-лого:                     # Логотипы магазинов-партнёров
        taggsm.webp, profi.webp, liberty.webp, greenSpark.webp, divizion.webp
```

## Соглашения

- **shared/** не импортирует ничего из features/, widgets/, models/ — только внешние библиотеки
- **api/axios.ts** — единственная точка входа для HTTP-запросов
- **Изображения** — `.webp`, импорт через `import img from '@/shared/assets/images/file.webp'`, использование как `img.src`
- **SVG-иконки** — инлайном в `IconSVG.tsx` (не вынесены в отдельные .svg файлы)
- **cn()** — для условных Tailwind-классов (использует clsx + tailwind-merge)
