---
description: Конвенции фронтенда BScout (Next.js 14 + FSD). Авто-подгружается при правке frontend-файлов.
paths: ["frontend/**/*.ts", "frontend/**/*.tsx", "frontend/**/*.css"]
---

# Правила фронтенда (Next.js 14, FSD)

## Архитектура слоёв
- `app/` — страницы App Router (`layout.tsx`, `page.tsx`, `globals.css`).
- `models/<entity>/` — слой данных, ровно 4 файла: `schema.ts` (Zod-схемы + выводимые типы), `service.ts` (вызовы через `api` из `@/shared/api/axios`), `hooks.ts` (React Query `useQuery`/`useMutation`), `index.ts` (barrel-экспорт). Новую сущность добавлять строго в этой форме — используй скил `/frontend-entity`.
- `widgets/` — композиционные блоки (Header = `"use client"`, Footer = server component).
- `shared/` — `api/axios.ts`, `config/query-client.ts`, `config/store.ts` (Effector), `providers/`, `ui/IconSVG.tsx`, `lib/utils.ts` (`cn()`), `assets/images/`.

## Состояние
- **Серверное состояние** — только React Query (через `models/*/hooks.ts`). Не дублировать в Effector.
- **Клиентское состояние авторизации** — Effector-сторы в `shared/config/store.ts`.
- JWT (`access_token` / `refresh_token`) живут в `localStorage`; их читает/обновляет axios-интерцептор в `shared/api/axios.ts` (авто-refresh на 401 → редирект на `/login`).

## Стиль кода
- `"use client"` — только если есть React-хуки; иначе Server Component.
- Импорты через алиас `@/*` (→ `src/`), не относительные `../../`.
- Стили — только Tailwind utility-классы; никаких `.css`/`.scss`-модулей. Цвета/шрифты/анимации — в `tailwind.config.ts`, не хардкодить.
- Условные классы — через `cn()` из `@/shared/lib/utils`.
- Изображения — `import img from '@/shared/assets/images/x.webp'`, использовать `img.src`.

## Дизайн
- Для любой UI/вёрстки — сначала прочитать дизайн-систему (скил `/design-system`, файлы в `skills/claude/`).
- Токены (CSS-переменные в `src/app/globals.css`, имена Tailwind в `tailwind.config.ts`):
  - поверхности — `ivory` `#FAF9F5`, `ivory-elevated` `#F0EEE6`, `ivory-warm` `#E3DACC`;
  - тёмные/текст — `slate` `#141413`, `slate-soft`, `slate-medium`, `body` `#3D3D3A`, `body-subtle`, `body-muted`;
  - границы — `border-default` `#B0AEA5`, `border-light`, `border-subtle`, `border-light-subtle`;
  - акценты (фиксированный hex, не переменные) — `clay` `#D97757`, `clay-ember`, `olive`, `sky`, `fig`, `cactus`, `green-discount`.
- Шрифты: `font-raleway` (основной), `font-dm-sans`, `font-lexend`, `font-montserrat`.
- Тёмная тема — `darkMode: 'class'`: переменные переопределяются в `.dark`, а не через `prefers-color-scheme`. Цвета вручную не свапать.
- Кнопки — готовые классы из `globals.css` (`.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger`, `.btn-sm/lg/icon/arrow`), не собирать заново.
- Старые токены `brand-dark #010D3E` / `muted #6F6C90` / `accent #b8007b` **устарели** — их нет в `tailwind.config.ts`. Они ещё встречаются в легаси `.scss`-модулях виджетов и в `DESIGN.md`/`README.md`; в новом коде не использовать.

## После правок
- `cd frontend && npm run build && npm run lint`.
