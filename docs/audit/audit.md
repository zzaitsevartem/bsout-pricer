# Аудит проекта BScout

Дата: 2026-07-13

---

## 1. Общее состояние

| Компонент | Статус |
|-----------|--------|
| Backend (FastAPI) | Реализована полная структура, 29 эндпоинтов, 12 модулей, 7 моделей |
| Frontend (Next.js) | 11 страниц свёрстано (mock-данные), shadcn/ui не установлен |
| Docker (PostgreSQL + Redis) | Готов (docker-compose.yml) |
| Миграции (Alembic) | НЕ настроены |
| Интеграция фронта и бэка | НЕ реализована |
| Парсеры | Базовая инфраструктура готова, реальных парсеров нет |

---

## 2. Backend — что реализовано

### 2.1 Структура (модульная MVC)

```
backend/src/
├── main.py                    # FastAPI app + CORS + RateLimit + 10 роутеров
├── config.py                  # pydantic-settings из .env
├── database.py                # async engine + session + Base + get_db
├── middleware/
│   ├── rate_limit.py          # IP-based rate limiter (120 req/min)
│   └── subscription_guard.py  # Guard для проверки подписки (не используется)
└── modules/
    ├── shared/deps.py         # get_current_user, get_current_admin (JWT)
    ├── health/                # GET /api/health
    ├── auth/                  # Регистрация, логин, refresh, logout
    ├── users/                 # Профиль, подписка
    ├── stores/                # CRUD магазинов (admin)
    ├── categories/            # CRUD категорий (admin)
    ├── products/              # Поиск товаров с фильтрами, история цен
    ├── search/                # История поиска
    ├── admin/                 # Статистика, управление пользователями
    ├── payment/               # Заглушка оплаты (создание/отмена подписки)
    ├── parser/                # Базовая инфраструктура (BaseParser, ParserManager)
    └── cache/                 # Redis cache сервис
```

### 2.2 Модели БД (7 моделей)

| Модель | Таблица | Связи |
|--------|---------|-------|
| User | users | 1:N -> Subscription, 1:N -> SearchHistory |
| Subscription | subscriptions | N:1 -> User |
| Store | stores | 1:N -> Product |
| Category | categories | 1:N -> Product |
| Product | products | N:1 -> Store, N:1 -> Category, 1:N -> PriceHistory |
| PriceHistory | price_history | N:1 -> Product |
| SearchHistory | search_history | N:1 -> User |

### 2.3 Эндпоинты (29 total)

**Публичные (6):**
| Метод | Путь |
|--------|------|
| GET | /api/health |
| POST | /api/auth/register |
| POST | /api/auth/login |
| POST | /api/auth/refresh |
| GET | /api/stores |
| GET | /api/categories |

**Требуют аутентификации (11):**
| Метод | Путь |
|--------|------|
| POST | /api/auth/logout |
| GET | /api/users/me |
| PATCH | /api/users/me |
| GET | /api/users/me/subscription |
| POST | /api/users/me/subscription |
| GET | /api/products |
| GET | /api/products/{id} |
| GET | /api/products/{id}/price-history |
| GET | /api/search/history |
| POST | /api/payment/subscribe |
| POST | /api/payment/cancel |

**Требуют прав администратора (12):**
| Метод | Путь |
|--------|------|
| POST | /api/stores |
| PATCH | /api/stores/{id} |
| POST | /api/categories |
| PATCH | /api/categories/{id} |
| GET | /api/admin/stats |
| GET | /api/admin/users |
| GET | /api/admin/users/{id} |
| POST | /api/admin/users/{id}/toggle-active |
| GET | /api/admin/parsers |
| POST | /api/admin/parsers/run |
| GET | /api/stores/{id} |
| GET | /api/categories/{id} |

### 2.4 Аутентификация

- JWT access token (15 мин) + refresh token (30 дней)
- bcrypt (passlib) для паролей
- Bearer token через HTTPAuthorizationCredentials
- Refresh token blacklist через Redis (проверка на /refresh)
- logout пока не пишет в blacklist

### 2.5 Инфраструктура

- Docker: PostgreSQL 16 + Redis 7
- Poetry для зависимостей
- Rate limiting: 120 запросов/мин по IP
- Redis cache: get/set/delete/exists/expire с TTL и JSON

---

## 3. Frontend — что реализовано

### 3.1 Страницы (11 total)

| Роут | Страница | Статус |
|------|----------|--------|
| `/` | Главная (лендинг) | ✅ Готов |
| `/login` | Вход | ✅ Вёрстка |
| `/register` | Регистрация | ✅ Вёрстка |
| `/search` | Поиск запчастей | ✅ Вёрстка |
| `/product` | Детальная товара | ✅ Вёрстка |
| `/tariffs` | Сравнение тарифов | ✅ Вёрстка |
| `/faq` | FAQ | ✅ Вёрстка |
| `/contacts` | Контакты | ✅ Вёрстка |
| `/account` | Личный кабинет | ✅ Вёрстка |
| `/subscription` | Управление подпиской | ✅ Вёрстка |
| `/admin` | Админ-панель | ✅ Вёрстка |

### 3.2 Дизайн-система

- Tailwind CSS с кастомными цветами (ivory, slate, clay, olive, sky, fig), шрифтами (Raleway, DM Sans, Lexend, Montserrat), анимациями (scroll, shimmer)
- Google Fonts подключены
- Адаптивность: max-md, max-lg, max-[480px]
- Прокси `/api/*` -> `localhost:8000`

### 3.3 Виджеты

- Header (client component, sticky, бургер-меню)
- Footer (server component, 4 колонки)
- Hero (Canvas-эффект "дырок", CTA)
- Carousel (бегущая строка партнёров)
- Advantages (3 карточки)
- Dashboard (с mockup-таблицей)
- Prices (3 тарифа, featured подсветка)
- BannerAccount (финальный CTA)

---

## 4. Что НЕ реализовано / требует доработки

### 4.1 Backend (срочное)

| # | Задача | Приоритет |
|---|--------|-----------|
| 1 | **Alembic** — настроить миграции (alembic.ini, env.py, первая миграция) | HIGH |
| 2 | **Logout реальный** — запись refresh токена в Redis blacklist при logout | HIGH |
| 3 | **SubscriptionGuard** — прикрутить к роутам продуктов (search по тарифам) | HIGH |
| 4 | **Fuzzy search** — pg_trgm для продвинутого тарифа (ILIKE уже есть) | HIGH |
| 5 | **Redis кэш поиска** — кэшировать результаты ProductService.search() | MEDIUM |
| 6 | **Реальные парсеры** — TGSM, Profi, Liberty, GreenSpark, Divizion | HIGH |
| 7 | **Seed data** — скрипты для наполнения stores, categories, admin user | MEDIUM |
| 8 | **CORS** — добавить поддержку production origin'ов | LOW |
| 9 | **Logging** — добавить structured logging | MEDIUM |
| 10 | **Error handling** — глобальный exception handler | MEDIUM |
| 11 | **Pagination helper** — вынести общую пагинацию в shared | LOW |
| 12 | **Soft delete** — добавить deleted_at для User | LOW |

### 4.2 Frontend (срочное)

| # | Задача | Приоритет |
|---|--------|-----------|
| 1 | **shadcn/ui** — установить компоненты (Button, Card, Input, etc.) | HIGH |
| 2 | **lib/utils.ts** — создать с функцией cn() | HIGH |
| 3 | **API-интеграция** — подключить все страницы к реальным /api/* эндпоинтам | HIGH |
| 4 | **Аутентификация** — JWT логика на фронте (login, register, token storage) | HIGH |
| 5 | **Глобальный layout** — вынести Header/Footer в root layout | MEDIUM |
| 6 | **Auth Context** — React Context для пользователя и токенов | HIGH |
| 7 | **Формы** — валидация (react-hook-form + zod), отправка на API | HIGH |
| 8 | **Loading states** — skeleton, spinner, loading.tsx | MEDIUM |
| 9 | **Error boundaries** — глобальная обработка ошибок | MEDIUM |
| 10 | **SEO** — per-page metadata | LOW |
| 11 | **Legacy SCSS** — удалить 7 файлов .module.scss (~2400 строк) | LOW |
| 12 | **Header navCta** — исправить тип (добавить 'both') | LOW |
| 13 | **Lucide icons** — заменить inline SVG на lucide-react | LOW |
| 14 | **DecorativeLines** — подключить или удалить | LOW |
| 15 | **Дубликаты img/ и public/** — синхронизировать или удалить img/ | LOW |

### 4.3 Инфраструктура

| # | Задача | Приоритет |
|---|--------|-----------|
| 1 | **Dockerfile backend** — создать для прода | MEDIUM |
| 2 | **Dockerfile frontend** — создать для прода (Next.js standalone) | MEDIUM |
| 3 | **Full-stack docker-compose** — добавить backend/frontend сервисы | MEDIUM |
| 4 | **Nginx** — конфигурация для прода | LOW |
| 5 | **CI/CD** — GitHub Actions (lint, test, build) | LOW |

---

## 5. План дальнейших работ (по этапам)

### Этап 2.1 — Backend API (завершение)
- [ ] Настроить Alembic + создать первую миграцию
- [ ] Реализовать logout (Redis blacklist)
- [ ] Прикрутить SubscriptionGuard к products/search
- [ ] Написать seed-скрипты (stores, categories, admin)
- [ ] Добавить глобальный exception handler

### Этап 2.2 — Frontend API-интеграция
- [ ] Установить shadcn/ui, создать cn()
- [ ] Реализовать AuthContext (JWT логика)
- [ ] Интегрировать login/register с /api/auth/*
- [ ] Интегрировать поиск с /api/products
- [ ] Интегрировать профиль с /api/users/me
- [ ] Интегрировать админку с /api/admin/*

### Этап 3 — Парсеры
- [ ] Реализовать TGSM парсер
- [ ] Реализовать Profi парсер
- [ ] Реализовать Liberty парсер
- [ ] Реализовать GreenSpark парсер
- [ ] Реализовать Divizion парсер
- [ ] Настроить расписание (arq/RQ + Redis)

### Этап 4-7 — Premium и Production
- [ ] Fuzzy search (pg_trgm)
- [ ] Dockerfile (backend + frontend)
- [ ] Full-stack docker-compose
- [ ] Nginx
- [ ] CI/CD

---

## 6. Сводка

```
Backend:    29/29 эндпоинтов = 100% (реализовано)
Frontend:   11/11 страниц = 100% (вёрстка), 0% (API-интеграция)
Модели БД:  7/7 = 100%
Парсеры:    0/5 = 0%
Alembic:    0%
Миграции:   0/1 = 0%
Docker:     2/4 сервисов = 50% (только PG + Redis, нет backend/frontend)
CI/CD:      0%
```

Рекомендуемый фокус: **Alembic + shadcn/ui + AuthContext + интеграция login/register** — это разблокирует дальнейшую разработку.
