# DESIGN.md — BScout

Описание архитектуры, стилей, компонентов и соглашений проекта для AI-агентов.

---

## 1. Общий обзор

BScout — веб-платформа для поиска и сравнения цен на запчасти для электроники (телефоны, ноутбуки, etc.) среди локальных магазинов г. Ставрополя. Подписочная модель (Пробный / Базовый / Продвинутый).

- **Фронтенд:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS v3, shadcn/ui, FSD (Feature-Sliced Design)
- **Бэкенд:** FastAPI (Python), SQLAlchemy 2.0 (async), Alembic, PostgreSQL 16, Redis 7
- **Инфраструктура:** Docker (PostgreSQL + Redis), прокси `/api/*` → `localhost:8000`

---

## 2. Дизайн-токены

### 2.1 Цветовая система

| Token | Hex | Использование |
|-------|-----|---------------|
| `brand-dark` | `#010D3E` | Тёмный текст, заголовки |
| `brand-gradient` | `linear-gradient(#000000, #001354)` | Фоновый градиент |
| `muted` | `#6F6C90` | Вторичный текст |
| `muted-dark` | `#FFFFFF99` | Белый текст с прозрачностью |
| `gray-custom` | `#7B7B7B` | Иконки соцсетей, серая графика |
| `border-light` | `#E6E6E6` | Границы карточек |
| `accent-pink` | `#b8007b` | Активный пункт меню, ховеры ссылок |
| `accent-hover` | `#a3bbfd` | Ховер кнопок (белый текст на чёрном) |
| `green-discount` | `#22c55e` | Текст скидки на тарифах |

### 2.2 Градиенты

- `hero-gradient`: `linear-gradient(220deg, #ffffff 65%, rgba(114, 127, 212, 0.56) 100%)` — фон секции Advantages
- `dashboard-gradient`: `linear-gradient(270deg, #D2DCFF 0%, #ffffff 17%, #ffffff 83%, #D2DCFF 100%)` — фон Dashboard
- `banner-gradient`: `linear-gradient(#ffffff, #cfd6ff)` — фон BannerAccount
- `hero-bg`: `linear-gradient(190deg, #EAEEFE 60%, #001ED5 100%)` — фон Hero
- Header bg: `#EAEEFE`

### 2.3 Типографика

| Шрифт | Назначение | Подключение |
|-------|-----------|-------------|
| `Raleway` | Основной (body, заголовки), 400/700/900 | Google Fonts |
| `DM Sans` | Дополнительный (цены, подписи), 100–1000 | Google Fonts |
| `Lexend` | Дополнительный, 100–900 | Google Fonts |
| `Montserrat` | Дополнительный, 100–900 | Google Fonts |

Базовый размер: `1rem = 16px`. `<body>`: `font-family: 'Raleway', Arial, sans-serif`.

### 2.4 Анимации

| Анимация | CSS/Keyframes | Применение |
|----------|---------------|------------|
| `smoothGlow` | 4s linear infinite, переливание тени по 4 сторонам | Логотип в Footer (LogoB) |
| `scroll` | 20s linear infinite, translateX(0 → -33.333%) | Карусель логотипов партнёров |
| Header | shadow-md при скролле (`isScrolled`) | Sticky header |
| Бургер | rotate/opacity гамбургер → крестик | Mobile menu |
| Mobile menu | translate-x-full → translate-x-0 | Slide-in меню |
| Кнопки | hover: -translate-y-0.5, hover: shadow-lg | Hero CTA |
| Ссылки | hover: translate-x-1 (Arrow) | Hero "Подробнее" |

---

## 3. Архитектура проекта

### 3.1 Корневая структура

```
bscout/
├── backend/            # FastAPI приложение
│   └── src/
│       ├── main.py     # Точка входа, CORS, health
│       ├── config.py   # (TODO) pydantic-settings
│       ├── database.py # (TODO) async SQLAlchemy
│       ├── models/     # (TODO) SQLAlchemy модели
│       ├── schemas/    # (TODO) Pydantic схемы
│       ├── api/        # (TODO) Роутеры
│       ├── services/   # (TODO) Бизнес-логика
│       ├── parsers/    # (TODO) Парсеры магазинов
│       └── utils/      # (TODO) Вспомогательные функции
├── docker/
│   └── docker-compose.yml  # PostgreSQL 16 + Redis 7
├── docs/
│   ├── technical-specification.md  # Полное ТЗ
│   └── bussines-plan.md           # Бизнес-план
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   │   ├── layout.tsx # Root layout (metadata, fonts)
│   │   │   ├── page.tsx   # Главная: Header + HomeWidget + Footer
│   │   │   └── globals.css # Tailwind + CSS variables + Google Fonts
│   │   ├── components/ui/ # shadcn/ui компоненты
│   │   ├── widgets/       # FSD: виджеты
│   │   │   ├── Header/    # "use client" — sticky header
│   │   │   ├── Footer/    # Server component
│   │   │   └── homeWidget/ui/ # Hero, Carousel, Advantages, Dashboard, Prices, BannerAccount
│   │   ├── shared/
│   │   │   ├── ui/IconSVG.tsx  # Все SVG-иконки
│   │   │   └── assets/images/  # .webp изображения
│   │   └── lib/utils.ts  # cn() — Tailwind class merge
│   ├── tailwind.config.ts  # Цвета, шрифты, keyframes, animations
│   ├── next.config.mjs     # Proxy /api/* → localhost:8000
│   └── components.json     # shadcn/ui config
└── DESIGN.md  ← этот файл
```

### 3.2 frontend/src (FSD)

```
src/
├── app/                     # Next.js App Router слой
│   ├── layout.tsx           # html lang="ru", metadata, globals.css
│   └── page.tsx             # Home page (Header + HomeWidget + Footer)
├── components/ui/           # shadcn/ui: button, card, carousel, navigation-menu
├── widgets/                 # Композиционные блоки
│   ├── Header/ui/Header.tsx        # "use client" — usePathname, useState
│   ├── Footer/ui/Footer.tsx        # Server — Link, a, соцсети
│   └── homeWidget/ui/
│       ├── index.tsx               # Композиция всех секций
│       ├── Hero/Hero.tsx           # Server — CTA, заголовок, декоративные фигуры
│       ├── Carousel/Carousel.tsx   # Server — animate-scroll, 5 партнёров
│       ├── Advantages/Advantages.tsx # Server — 3 карточки с иконками
│       ├── Dashboard/Dashboard.tsx # Server — скриншот + декоративные фигуры
│       ├── Prices/Prices.tsx       # Server — 3 тарифа, CheckMark
│       └── BannerAccount/BannerAccount.tsx # Server — финальный CTA
├── shared/
│   ├── ui/IconSVG.tsx       # Logo, LogoB, PersonIcon, SupportIcon, Arrow, CheckMark, TgIcon, VkIcon
│   └── assets/images/       # Все .webp изображения
└── lib/utils.ts             # cn() функция
```

### 3.3 Статус компонентов

| Компонент | "use client"? | Состояние |
|-----------|---------------|-----------|
| Header | Да (usePathname, useState) | ✅ Готов |
| Footer | Нет | ✅ Готов |
| Hero | Нет | ✅ Готов |
| Carousel | Нет | ✅ Готов |
| Advantages | Нет | ✅ Готов |
| Dashboard | Нет | ✅ Готов |
| Prices | Нет | ✅ Готов |
| BannerAccount | Нет | ✅ Готов |

**Правило:** `"use client"` ставим только если есть React-хуки (useState, useEffect, usePathname). Все виджеты, которые не требуют интерактивности, — Server Components.

---

## 4. API и данные

### 4.1 Прокси

В `next.config.mjs`: все запросы к `/api/*` проксируются на `http://localhost:8000/api/*`.

Пример: `fetch('/api/products?q=дисплей')` → `http://localhost:8000/api/products?q=дисплей`

### 4.2 Эндпоинты (текущие)

| Метод | Путь | Статус |
|-------|------|--------|
| GET | `/api/health` | ✅ Готов (FastAPI) |

### 4.3 Эндпоинты (планируемые)

См. полный список в `docs/technical-specification.md` (секция 3.3):
- `/api/auth/*` — регистрация, логин, JWT
- `/api/users/*` — профиль, подписка, история
- `/api/products` — поиск, детали, история цен
- `/api/stores`, `/api/categories` — публичные
- `/api/admin/*` — админка

---

## 5. Тарифы и подписки

| Тариф | Цена | Товары | Поставщики | Обновление | Особенности |
|-------|------|--------|------------|------------|-------------|
| Пробный | 0₽ / 10 дн | до 10 | 2 | 24ч | История цен 1 мес |
| Базовый | 399₽ / мес | до 100 | 15+ | 6ч | PDF/CSV, поддержка 24/7 |
| Продвинутый | 499₽ / мес | безлимит | 50+ | real-time | API, fuzzy search, аналитика, менеджер |

**Скидка 20% на первый платёж** любого платного тарифа.

---

## 6. Изображения

Все изображения в `frontend/src/shared/assets/images/` (формат .webp).

| Файл | Назначение |
|------|------------|
| `figureCylinder.webp` | Декоративный цилиндр (Hero) |
| `figurePiramid.webp` | Декоративная пирамида (Hero, Dashboard) |
| `figureHaifTorus.webp` | Декоративный полуторус (Hero) |
| `greenSpark.webp` | Логотип GreenSpark (Carousel) |
| `taggsm.webp` | Логотип ТГСМ (Carousel) |
| `divizion.webp` | Логотип Дивизион (Carousel) |
| `liberty.webp` | Логотип Либерти (Carousel) |
| `profi.webp` | Логотип Профи (Carousel) |
| `helix.webp` | Иконка "Актуальная информация" (Advantages) |
| `vurtel.webp` | Иконка "Гибкость" (Advantages) |
| `cube.webp` | Иконка "Экономия времени" (Advantages) |
| `torus.webp` | Декоративный торус (Dashboard) |
| `dashboard.webp` | Скриншот дашборда (Dashboard) |
| `emojiStar.webp` | Декоративная звезда (BannerAccount) |
| `helixTwo.webp` | Декоративная спираль (BannerAccount) |
| `logo1.webp` | Favicon |

**Важно:** изображения импортируются как StaticImageData и используются через `.src` (Next.js 14 App Router не поддерживает прямую строку с путём).

---

## 7. Иконки (SVG)

Все иконки в `frontend/src/shared/ui/IconSVG.tsx`.

| Компонент | SVG-путь | Использование |
|-----------|----------|---------------|
| `<Logo />` | Текстовый логотип "BScout" + заяц | Header |
| `<LogoB />` | Квадратный логотип с градиентной "B" | Footer |
| `<PersonIcon />` | Иконка профиля | Header |
| `<SupportIcon />` | Иконка поддержки (гарнитура) | Header |
| `<Arrow />` | Стрелка вправо | Hero, BannerAccount |
| `<CheckMark />` | Галочка | Prices (список фич) |
| `<TgIcon />` | Telegram | Footer |
| `<VkIcon />` | VK | Footer |

Принцип: все SVG-компоненты принимают `React.SVGProps<SVGSVGElement>`, что позволяет переопределять `width`, `height`, `color`, `fill`, `className`.

---

## 8. Роутинг (Next.js App Router)

### Реализованные маршруты

| Path | Компонент | Статус |
|------|-----------|--------|
| `/` | `app/page.tsx` (Header + HomeWidget + Footer) | ✅ |

### Планируемые маршруты

| Path | Страница |
|------|----------|
| `/search` | Поиск товаров |
| `/search?q=...` | Поиск с запросом |
| `/product/:id` | Детальная страница товара |
| `/account` | Личный кабинет |
| `/account/subscription` | Управление подпиской |
| `/account/history` | История поиска |
| `/login` | Вход |
| `/register` | Регистрация |
| `/tariffs` | Тарифы |
| `/faq` | FAQ |
| `/contacts` | Контакты |
| `/privacy` | Политика конфиденциальности |
| `/terms` | Условия использования |
| `/admin` | Админ-панель |

---

## 9. Адаптивность

Breakpoints (Tailwind default):

- `max-[480px]` — малые телефоны
- `max-md` (≤768px) — планшеты/телефоны
- `max-lg` (≤1024px) — планшеты
- `md` (≥768px) — десктоп-минимум
- `lg` (≥1024px) — десктоп

Подход: Desktop-first для секций Hero и Advantages; Mobile-first для навигации (бургер).

---

## 10. Соглашения для агентов

### 10.1 Стиль кода

- **Tailwind utility classes** — все стили inline, никаких CSS-модулей или SCSS
- **cn()** из `@/lib/utils` для условных классов (использует `clsx` + `tailwind-merge`)
- **"use client"** — минимально, только где нужны React-хуки (useState, useEffect, usePathname)
- **Импорты** — относительные (e.g. `../../shared/ui/IconSVG`)
- **shadcn/ui** — компоненты в `@/components/ui/`, конфиг в `components.json`

### 10.2 Стиль именования

- **Файлы:** `PascalCase` для компонентов (Header.tsx, Hero.tsx), `camelCase` для утилит (utils.ts)
- **Функции:** `camelCase`
- **Компоненты:** `PascalCase`
- **Экспорт:** именованный `export { Header }` или `export default Hero`

### 10.3 Типы

```typescript
// shadcn компоненты через cn() + VariantProps из class-variance-authority
// SVG-иконки: React.FC<React.SVGProps<SVGSVGElement>>
// Изображения: через StaticImageData → .src
```

### 10.4 Бэкенд-соглашения

- FastAPI async endpoints
- SQLAlchemy 2.0 async sessionmaker
- Pydantic v2 для схем
- Alembic для миграций
- JWT (access 15min + refresh 30d)
- Парсеры: асинхронные, модульные (класс-наследник Parser)

---

## 11. Состояние разработки

### Выполнено (Этап 1 — MVP)
- FSD-структура, Next.js App Router, Tailwind
- Все виджеты лендинга (Header, Footer, Hero, Carousel, Advantages, Dashboard, Prices, BannerAccount)
- FastAPI skeleton + health endpoint
- Docker (PostgreSQL + Redis)
- npm run build — успешно
- Горизонтальный скролл исправлен

### В работе (Этап 2 — Backend API)
- (none)

### Планируется
- Этап 2: SQLAlchemy модели, Alembic, Auth API, Users API, Products API, Admin API, Dockerfile
- Этап 3: Парсеры магазинов
- Этап 4: Страницы поиска, товара, аккаунта, админки
- Этап 5: Интеграция frontend ↔ backend
- Этап 6: Premium-фичи (fuzzy search, autocomplete, аналитика)
- Этап 7: Production (Docker Compose full stack, Nginx, CI/CD)

---

## 12. Ключевые ссылки

- ТЗ: `docs/technical-specification.md`
- Бизнес-план: `docs/bussines-plan.md`
- Docker compose: `docker/docker-compose.yml`
- Frontend entry: `frontend/src/app/layout.tsx`
- Tailwind config: `frontend/tailwind.config.ts`
- API proxy config: `frontend/next.config.mjs`
- Backend entry: `backend/src/main.py`
- Backend dependencies: `backend/requirements.txt`
