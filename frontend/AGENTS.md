# AGENTS.md — BScout Frontend

Инструкции для AI-агентов, работающих над фронтендом BScout.

## Команды

```bash
npm run dev     # Dev server на :3000
npm run build   # Проверить сборку
npm run lint    # ESLint
```

## Стек

- Next.js 14 (App Router), React 18, TypeScript 5
- Tailwind CSS v3 — все стили только через utility classes (никаких .css/.scss модулей)
- shadcn/ui — компоненты в `src/components/ui/`
- FSD (Feature-Sliced Design) — `widgets/`, `shared/`, `components/ui/`

## Структура FSD

```
src/
├── app/              # App Router: layout.tsx, page.tsx, globals.css
├── components/ui/    # shadcn/ui (button, card, navigation-menu, carousel)
├── widgets/          # Композиционные блоки
│   ├── Header/       # "use client" (usePathname, бургер)
│   ├── Footer/       # Server component
│   └── homeWidget/   # Hero, Carousel, Advantages, Dashboard, Prices, BannerAccount
└── shared/
    ├── ui/IconSVG.tsx # Все SVG (Logo, Arrow, CheckMark, TgIcon, VkIcon...)
    └── assets/images/ # .webp изображения (через StaticImageData → .src)
```

## Соглашения по коду

- **"use client"** — только если есть React-хуки (useState, useEffect, usePathname). Все остальные — Server Components
- **Импорты** — относительные (`../../shared/ui/IconSVG`)
- **cn()** из `@/lib/utils` для условных Tailwind-классов
- **SVG-иконки** — React.FC<React.SVGProps<SVGSVGElement>>, принимают width/height/color/className
- **Изображения** — `import img from '@/shared/assets/images/img.webp'`, использовать как `img.src`
- **Анимации** — в tailwind.config.ts (keyframes + animation). Не использовать styled-jsx
- **Цвета/шрифты** — через tailwind.config.ts, не хардкодить значения
- **Адаптивность** — Tailwind breakpoints (max-md, max-lg, lg, etc.)

## Ключевые файлы

- `tailwind.config.ts` — кастомные цвета, шрифты, keyframes
- `next.config.mjs` — прокси /api/* → localhost:8000
- `globals.css` — Tailwind directives, CSS variables, Google Fonts
- `components.json` — shadcn/ui конфиг
- `lib/utils.ts` — cn() функция

## Дизайн-токены (кратко)

- Цвет: brand-dark #010D3E, muted #6F6C90, accent #b8007b
- Шрифты: Raleway (осн.), DM Sans/Lexend/Montserrat (доп.)
- Градиенты: hero-gradient, dashboard-gradient, banner-gradient
- Анимации: smoothGlow (4s), scroll (20s)

## После изменений

Всегда запускать `npm run build && npm run lint` перед завершением работы.
