# BScout 🚀

Веб-платформа для поиска и сравнения цен на запчасти для мобильных телефонов, ноутбуков и электроники среди локальных магазинов г. Ставрополя 🔍💻📱

---

## 📌 О проекте

**BScout** — это городской ценовой агрегатор для техники и запчастей:
- 🧩 Парсим локальные магазины
- 📦 Собираем цены и наличие в единую базу
- 📊 Даём удобный поиск и сравнение предложений
- 💳 Внедряем аккаунты, подписки и premium-фишки

**Цель проекта:** сократить время поиска нужной запчасти/техники и помочь найти лучшую цену в своём городе.

---

## 🏗️ Архитектура и стек

### Общая архитектура

```text
┌────────────┐       ┌────────────┐       ┌────────────┐       ┌────────────┐
│  Frontend  │ ───▶  │   Backend  │ ───▶  │ PostgreSQL │       │   Redis    │
│ (Next.js)  │  API  │  (FastAPI) │  SQL  │     16     │       │     7      │
└────────────┘       └────────────┘       └────────────┘       └────────────┘
                           │                                        │
                           └────────── кэширование ────────────────┘
```

### Backend (API + Business Logic)

- 🐍 **Python 3.11+**
- ⚡ **FastAPI** — высокопроизводительный async-фреймворк
- 🗄️ **SQLAlchemy 2.0 (async)** + **asyncpg** — ORM и драйвер PostgreSQL
- 🔀 **Alembic** — миграции базы данных
- 🔐 **JWT-авторизация** (python-jose + passlib/bcrypt)
- 🧠 **Redis** — кэширование и быстрые состояния
- 📡 **httpx** — HTTP-клиент для внешних вызовов (парсеры, интеграции)

### Frontend (UI)

- ⚛️ **React 18** + **Next.js 14 (App Router)**
- 🎨 **Tailwind CSS** + **shadcn/ui** — дизайн-система
- 🧱 **FSD (Feature-Sliced Design)** — архитектура фронтенда
- 📐 **TypeScript** — типизация
- 🔄 **TanStack React Query** — серверное состояние
- 🌐 **Axios** — HTTP-клиент
- 📝 **React Hook Form** + **Zod** — формы и валидация
- 🎭 **Radix UI** — доступные UI-примитивы
- 🗂️ **Effector** — 상태 приложения (state manager)

### Database & Cache

- 🐘 **PostgreSQL 16** — основная реляционная БД
- 💾 **Redis 7** — кэширование, сессии, очереди

### Инфраструктура

- 🐳 **Docker Compose** — локальная среда (Postgres + Redis)
- 📦 **Poetry** — управление зависимостями Python
- 📦 **npm** — управление зависимостями JS

---

## 📦 Библиотеки и зависимости

### Backend (`backend/pyproject.toml`)

| Библиотека | Версия | Назначение | Где используется |
|---|---|---|---|
| `fastapi` | ^0.115.0 | 🌐 Async-веб-фреймворк для построения REST API | Все эндпоинты (`/api/auth`, `/api/users`, `/api/health`), автоматическая генерация Swagger-документации, валидация запросов через Pydantic |
| `uvicorn[standard]` | ^0.30.0 | 🚀 ASGI-сервер высокой производности | Запуск приложения FastAPI в dev (`--reload`) и production режимах, обработка async/await |
| `sqlalchemy` | ^2.0.35 | 🗄️ Async ORM для работы с реляционными БД | Определение моделей `User`, `Subscription`, `Product`, `Store`, `PriceHistory`; запросы к БД через async-сессии |
| `asyncpg` | ^0.30.0 | 🐘 Async-драйвер PostgreSQL | Физическое подключение к PostgreSQL, выполнение SQL-запросов через SQLAlchemy engine |
| `redis` | ^5.1.0 | 💾 Клиент для Redis | Кэширование результатов поиска, хранение сессий, rate-limiting, очереди обновления цен |
| `alembic` | ^1.13.0 | 🔀 Система миграций для SQLAlchemy | Создание и применение миграций БД (`alembic revision --autogenerate`, `alembic upgrade head`) |
| `python-dotenv` | ^1.0.1 | ⚙️ Загрузка переменных окружения из `.env` | Чтение `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET` и других настроек при старте приложения |
| `pydantic` | ^2.9.0 | 📐 Валидация данных и сериализация | Определение схем запросов/ответов (`RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse`) |
| `pydantic-settings` | ^2.5.0 | 🔧 Управление конфигурацией через env | Класс `Settings` в `config.py` — типизированный доступ к `.env` переменным |
| `passlib[bcrypt]` | ^1.7.4 | 🔑 Хеширование паролей (bcrypt) | `auth/service/auth.py` — хеширование при регистрации, проверка при логине |
| `python-jose[cryptography]` | ^3.3.0 | 🔐 Создание и валидация JWT-токенов | Генерация access/refresh токенов при логине, проверка токена в `get_current_user` |
| `httpx` | ^0.27.0 | 📡 Async HTTP-клиент | Парсеры магазинов — запросы к внешним сайтам для сбора цен; webhook-интеграции |

### Frontend (`frontend/package.json`)

#### Основные зависимости

| Библиотека | Версия | Назначение | Где используется |
|---|---|---|---|
| `next` | ^14.2.0 | ⚡ React-фреймворк с App Router (SSR/SSG) | `app/` directory —роутинг страниц, layout, server/client components, API-прокси (`/api/*` → backend) |
| `react` | ^18.3.1 | ⚛️ Библиотека для построения UI | Все компоненты: виджеты (`Header`, `Footer`, `homeWidget`), UI-компоненты, страницы |
| `react-dom` | ^18.3.1 | 🖼️ Рендеринг React-компонентов в DOM | Точка входа `app/layout.tsx`, гидрация SSR → CSR |
| `typescript` | ^5.4.0 | 📝 Статическая типизация JavaScript | Все `.ts`/`.tsx` файлы — типизация пропсов, стейта, API-ответов, ошибок |
| `tailwindcss` | ^3.4.19 | 🎨 Utility-first CSS-фреймворк | Все стили проекта через utility-классы (`className="flex items-center gap-4"`), кастомные цвета/анимации в `tailwind.config.ts` |
| `@tanstack/react-query` | ^5.101.2 | 🔄 Управление серверным состоянием | Кэширование API-запросов, автоматический refetch, optimistic updates для данных пользователя |
| `axios` | ^1.18.1 | 🌐 HTTP-клиент для запросов к API | `shared/api/` — все запросы к backend (`/api/auth/*`, `/api/users/*`), интерцепторы для JWT |
| `effector` | ^23.4.4 | 🗂️ Менеджер состояний (state manager) | Глобальное состояние приложения: пользователь, авторизация, UI-состояния (мобильное меню, модалки) |
| `effector-react` | ^23.3.0 | 🔄 React-биндинги для Effector | Хуки `useUnit()` для подписки на сторы и вызова эффектов в React-компонентах |
| `react-hook-form` | ^7.81.0 | 📝 Управление формами | Формы регистрации, логина, обновления профиля, оформления подписки — управление стейтом полей |
| `@hookform/resolvers` | ^5.4.0 | 🔗 Интеграция Zod ↔ React Hook Form | Валидация форм: автоматическая проверка данных по Zod-схеме при сабмите |
| `zod` | ^4.4.3 | ✅ Декларативная валидация схем данных | Определение правил валидации: email, пароль, имя, телефон — переиспользуется и на фронте, и на бэке |
| `sass` | ^1.101.0 | 💅 Препроцессор SCSS | Запасной вариант для сложных стилей (проект преимущественно на Tailwind) |

#### UI-компоненты (shadcn/ui / Radix)

| Библиотека | Версия | Назначение | Где используется |
|---|---|---|---|
| `@radix-ui/react-navigation-menu` | ^1.2.14 | 🧭 Доступное навигационное меню | `Header` — основная навигация сайта, поддержка клавиатуры и скринридеров |
| `@radix-ui/react-slot` | ^1.2.4 | 🧩 Композиция компонентов через пропсы | `shadcn/ui` кнопки и ссылки — передача `asChild` для рендеринга как `<a>`, `<button>`, `<Link>` |
| `@radix-ui/react-visually-hidden` | ^1.2.4 | ♿ Скрытие текста для скринридеров | Доступность: описание иконок и интерактивных элементов для assistive technology |
| `class-variance-authority` | ^0.7.1 | 🎛️ Управление вариантами стилей компонентов | `shadcn/ui` — варианты кнопок (`default`, `outline`, `ghost`), инпутов, карточек |
| `clsx` | ^2.1.1 | 🔀 Условная конкатенация CSS-классов | Утилита `cn()` — условные классы: `clsx("base", isActive && "active", className)` |
| `tailwind-merge` | ^3.6.0 | 🧹 Мерж Tailwind-классов без конфликтов | Утилита `cn()` — предотвращение дублирования (`"px-4 px-8"` → `"px-8"`), переопределение базовых стилей |
| `embla-carousel-react` | ^8.6.0 | 🎠 Карусель/слайдер изображений | `homeWidget/Carousel` — промо-баннеры, галерея товаров на главной странице |
| `lucide-react` | ^1.24.0 | 🎭 Набор SVG-иконок | Иконки в UI: стрелки, крестики, иконки навигации, статусов, действий |

#### Dev-зависимости

| Библиотека | Версия | Назначение | Где используется |
|---|---|---|---|
| `@types/node` | ^20.17.0 | 📦 Типы для Node.js API | TypeScript: типизация `process.env`, `__dirname`, файловых операций |
| `@types/react` | ^18.3.0 | 📦 Типы для React | TypeScript: типизация `FC`, `PropsWithChildren`, хуков (`useState`, `useEffect`) |
| `@types/react-dom` | ^18.3.0 | 📦 Типы для ReactDOM | TypeScript: типизация `createRoot`, `hydrateRoot`, `Portal` |
| `autoprefixer` | ^10.5.0 | 🔧 Автоматические CSS-префикты | PostCSS-плагин: добавление `-webkit-`, `-moz-` префиксов для кроссбраузерности |
| `eslint-config-next` | ^14.2.0 | 🔍 Линтер кода (ESLint) | Проверка ошибок, стиля и потенциальных проблем в `.ts`/`.tsx` файлах |
| `postcss` | ^8.5.15 | 🔄 Трансформация CSS | Обработка Tailwind-директив (`@tailwind base/components/utilities`) перед компиляцией |
| `prettier` | ^3.9.5 | ✨ Форматирование кода | Единый стиль: `npm run format` — автоформатирование `.ts`/`.tsx` файлов |

---

## 📂 Структура проекта

```text
bscout/
├── frontend/                  # 🖥️ Next.js 14 + Tailwind + shadcn/ui + FSD
│   ├── src/
│   │   ├── app/               # App Router (layout, pages, globals.css)
│   │   ├── widgets/           # FSD-виджеты (Header, Footer, homeWidget)
│   │   │   ├── Header/        # Навигация (client: usePathname, бургер)
│   │   │   ├── Footer/        # Подвал (server component)
│   │   │   └── homeWidget/    # Hero, Carousel, Advantages, Dashboard, Prices
│   │   ├── components/ui/     # shadcn/ui (button, card, carousel, nav-menu)
│   │   └── shared/            # Иконки (IconSVG), изображения, утилиты
│   ├── tailwind.config.ts     # Кастомные цвета, шрифты, анимации
│   ├── next.config.mjs        # Прокси /api/* → backend:8000
│   └── package.json
│
├── backend/                   # ⚙️ FastAPI + SQLAlchemy + Alembic
│   ├── src/
│   │   ├── main.py            # Точка входа FastAPI, CORS, роутеры
│   │   ├── config.py          # Настройки из .env (pydantic-settings)
│   │   ├── database.py        # Async engine + sessionmaker + Base
│   │   └── modules/           # Модульная архитектура (MVC)
│   │       ├── shared/        # Общие зависимости (get_current_user)
│   │       ├── health/        # GET /api/health
│   │       ├── auth/          # Регистрация, логин, JWT, модели User/Subscription
│   │       ├── users/         # Профиль, подписки
│   │       ├── admin/         # Админ-панель (TODO)
│   │       └── products/      # Товары и поиск (TODO)
│   ├── alembic/               # Миграции
│   ├── alembic.ini
│   └── pyproject.toml
│
├── docker/                    # 🐳 docker-compose.yml (PostgreSQL 16 + Redis 7)
├── docs/                      # 📄 Техническое задание и бизнес-план
└── README.md                  # 📖 Документация проекта
```

---

## 🚀 Быстрый старт

### 1. Поднять базы данных (Docker)

```bash
docker compose -f docker/docker-compose.yml up -d
```

После запуска будут доступны:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### 2. Настроить и запустить Backend

```bash
cd backend
cp .env.example .env          # Скопировать шаблон переменных
poetry install                # Установить зависимости
poetry run alembic upgrade head  # Применить миграции
poetry run uvicorn src.main:app --reload  # Запустить сервер
```

### 3. Настроить и запустить Frontend

```bash
cd frontend
npm install                   # Установить зависимости
npm run dev                   # Dev-сервер на :3000
```

### 4. Открыть в браузере

| Сервис | URL | Описание |
|---|---|---|
| 🖥️ Frontend | `http://localhost:3000` | Основной UI |
| ⚙️ Backend API | `http://localhost:8000` | REST API |
| 📖 Swagger Docs | `http://localhost:8000/docs` | Автоматическая документация API |
| 📖 ReDoc | `http://localhost:8000/redoc` | Альтернативная документация API |

---

## 🔧 Команды для разработки

### Frontend

```bash
cd frontend
npm run dev          # 🏃 Dev-сервер (HMR)
npm run build        # 📦 Production-сборка
npm run start        # 🚀 Запуск production-сборки
npm run lint         # 🔍 Проверка ESLint
npm run format       # ✨ Форматирование Prettier
npm run format:check # ✨ Проверка форматирования
```

### Backend

```bash
cd backend
poetry run uvicorn src.main:app --reload          # 🏃 Dev-сервер на :8000
poetry run alembic revision --autogenerate -m "msg"  # ➕ Создать миграцию
poetry run alembic upgrade head                   # ⬆️ Применить мигр��ции
```

### Docker

```bash
docker compose -f docker/docker-compose.yml up -d     # ▶️ Запустить
docker compose -f docker/docker-compose.yml down       # ⏹️ Остановить
docker compose -f docker/docker-compose.yml ps         # 📋 Статус контейнеров
```

---

## 🌐 API Endpoints

### Public (без авторизации)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/health` | Health check — проверка работоспособности API |
| `POST` | `/api/auth/register` | Регистрация нового пользователя |
| `POST` | `/api/auth/login` | Вход в аккаунт (получение JWT) |
| `POST` | `/api/auth/refresh` | Обновление access-токена через refresh-токен |

### Auth (требуется JWT Bearer Token)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/users/me` | Получить профиль текущего пользователя |
| `PATCH` | `/api/users/me` | Обновить профиль (имя, телефон, компания) |
| `GET` | `/api/users/me/subscription` | Текущая подписка |
| `POST` | `/api/users/me/subscription` | Оформить подписку |

### Авторизация

- 🔐 **JWT:** access token (15 мин) + refresh token (30 дней)
- 🔑 **Хеширование паролей:** bcrypt через passlib
- 📡 **Формат:** `Authorization: Bearer <token>`

---

## 💰 Тарифы

| Тариф | Цена | Товары | Поставщики | Частота обновления |
|---|---|---|---|---|
| 🆓 Пробный | 0 ₽ / 10 дней | до 10 | 2 | каждые 24ч |
| ⭐ Базовый | 399 ₽ / мес | до 100 | 15+ | каждые 6ч |
| 💎 Продвинутый | 499 ₽ / мес | безлимит | 50+ | real-time |

🎁 **Промо:** скидка 20% на первый платёж любого платного тарифа.

---

## 📊 Текущий статус проекта

### Общий прогресс

```
████████████████████████████████████████████████████████████░░░░░░░░░░░░░░░░░░░░  60%
```

**🟢 60% готово** | **40% впереди**

| Этап | Статус | Описание |
|---|---|---|
| Этап 1 — MVP | ✅ Готово | Лендинг, backend-скелет, Docker |
| Этап 2 — Auth/Users | ✅ Готово | Модели, JWT, регистрация, логин, профиль, подписки |
| Этап 2 — Миграции | ✅ Готово | Alembic, доработки API |
| Этап 3 — Парсеры | 🔄 В процессе | Парсинг магазинов и сбор цен |
| Этап 4 — Страницы | ⏳ Ожидание | Поиск, карточка товара, аккаунт |
| Этапы 5–7 | ⏳ Ожидание | Интеграции, premium, production |

---

## 📐 Дизайн-токены

| Параметр | Значение |
|---|---|
| Основной цвет | `#010D3E` (brand-dark) |
| Приглушённый | `#6F6C90` (muted) |
| Акцент | `#b8007b` (accent) |
| Основной шрифт | Raleway |
| Доп. шрифты | DM Sans, Lexend, Montserrat |

---

## 📏 Соглашения и рекомендации

- ⛔ **Не коммитить** без явной просьбы пользователя
- 📖 **Читать `DESIGN.md`** перед задачами по дизайну/UI
- 📖 **Читать `docs/technical-specification.md`** перед новой фичей
- ✅ **Запускать `npm run build && npm run lint`** после правок фронтенда
- 🐍 **snake_case** в Python, **camelCase** в JSON (через Pydantic)
- 🧩 **Модульность:** каждый модуль = model + schema + service + controller
- 🚫 **Не плодить** лишние doc-файлы без запроса
- 🔒 **.env** в `.gitignore`, шаблон в `.env.example`

---

## 📄 Лицензия

Проект находится в стадии разработки. Лицензия не определена.

---

> **BScout** = Next.js 14 ⚡ + FastAPI 🐍 + PostgreSQL 🐘 + Redis 💾 + Docker 🐳
> 
> Сравнивай цены. Экономь время. Выбирай лучшее 💪
