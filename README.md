# BScout

Веб-платформа для поиска и сравнения цен на запчасти для мобильных телефонов, ноутбуков и электроники среди локальных магазинов г. Ставрополя.

## Стек

| Компонент | Технология |
|-----------|-----------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui, FSD |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Инфраструктура | Docker, docker-compose, Poetry |

## Структура проекта

```
bscout/
├── frontend/          # Next.js 14 + Tailwind + shadcn/ui + FSD
│   └── src/
│       ├── app/       # App Router (layout, pages)
│       ├── widgets/   # FSD виджеты (Header, Footer, homeWidget)
│       ├── components/ui/  # shadcn/ui компоненты
│       └── shared/    # Иконки, изображения, утилиты
├── backend/           # FastAPI + SQLAlchemy + Alembic
│   └── src/
│       ├── main.py    # Точка входа
│       ├── config.py  # Настройки из .env
│       ├── database.py # Engine + session
│       └── modules/   # Модульная MVC-архитектура
│           ├── auth/      # Регистрация, логин, JWT
│           ├── users/     # Профиль, подписка
│           ├── health/    # Health check
│           ├── admin/     # Админ-панель (TODO)
│           └── products/  # Поиск товаров (TODO)
├── docker/            # docker-compose.yml (PostgreSQL + Redis)
└── docs/              # ТЗ и бизнес-план
```

## Быстрый старт

### 1. Запустить базы данных

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 2. Backend

```bash
cd backend
cp .env.example .env
poetry install
poetry run uvicorn src.main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Открыть

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## API Endpoints

| Method | Path | Описание | Доступ |
|--------|------|----------|--------|
| GET | `/api/health` | Health check | Public |
| POST | `/api/auth/register` | Регистрация | Public |
| POST | `/api/auth/login` | Вход | Public |
| POST | `/api/auth/refresh` | Обновление токена | Public |
| GET | `/api/users/me` | Профиль | Auth |
| PATCH | `/api/users/me` | Обновление профиля | Auth |
| GET | `/api/users/me/subscription` | Текущая подписка | Auth |
| POST | `/api/users/me/subscription` | Оформление подписки | Auth |

## Текущий статус

- ✅ **MVP (Этап 1)** — лендинг, backend skeleton, Docker
- ✅ **User + Auth (Этап 2, частично)** — модели, JWT, регистрация, логин, профиль, подписка
- 🔄 **Этап 2** — SQLAlchemy модели, Alembic, API (в процессе)
- ⏳ **Этап 3** — Парсеры магазинов
- ⏳ **Этап 4** — Страницы поиска, товара, аккаунта
- ⏳ **Этап 5-7** — Интеграция, premium-фичи, production

## Тарифы

| Тариф | Цена | Товары | Поставщики | Обновление |
|-------|------|--------|------------|------------|
| Пробный | 0₽ / 10 дн | до 10 | 2 | 24ч |
| Базовый | 399₽ / мес | до 100 | 15+ | 6ч |
| Продвинутый | 499₽ / мес | безлимит | 50+ | real-time |

Скидка 20% на первый платёж любого платного тарифа.
