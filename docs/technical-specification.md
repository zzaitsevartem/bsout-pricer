# Техническое задание — BScout

## 1. Общие сведения

### 1.1 Наименование проекта
BScout — веб-платформа для поиска и сравнения цен на запчасти для мобильных телефонов, ноутбуков и электроники среди локальных магазинов.

### 1.2 Цель проекта
Создать единый интерфейс для поиска запчастей по нескольким магазинам города Ставрополя с автоматическим сравнением цен, выделением самого дешёвого предложения и подписочной моделью доступа.

### 1.3 Целевая аудитория
- Сервисные центры по ремонту телефонов, ноутбуков и электроники (основной сегмент)
- Частные мастера по ремонту электроники
- Обычные пользователи, самостоятельно ремонтирующие устройства

---

## 2. Архитектура системы

### 2.1 Общая архитектура

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│        React 19 + TypeScript + CRA              │
│              FSD Architecture                    │
│         http://localhost:3000                    │
└──────────────────────┬──────────────────────────┘
                       │ HTTP (proxy)
┌──────────────────────▼──────────────────────────┐
│                   Backend                        │
│          FastAPI (Python 3.11+)                  │
│         http://localhost:8000                    │
└──────┬─────────────────────────────┬─────────────┘
       │                             │
┌──────▼──────┐            ┌─────────▼──────────┐
│  PostgreSQL  │            │       Redis        │
│    16 alpine │            │     7 alpine       │
│   порт 5432  │            │    порт 6379       │
└──────────────┘            └────────────────────┘
```

### 2.2 Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Frontend | React 19, TypeScript 4.9, SCSS Modules, react-router-dom 7 |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| База данных | PostgreSQL 16 |
| Кэш / очереди | Redis 7 |
| Контейнеризация | Docker, docker-compose |
| Парсинг | Modular parsers (per-store), aiohttp / httpx |

### 2.3 Требования к окружению

- Node.js 18+
- Python 3.11+
- Docker & docker-compose
- npm / yarn

---

## 3. Backend

### 3.1 Структура проекта

```
backend/
├── .env                    # Переменные окружения
├── .env.example            # Шаблон .env
├── requirements.txt        # Зависимости Python
├── alembic.ini             # Конфигурация Alembic
├── alembic/                # Миграции БД
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   ├── main.py             # Точка входа FastAPI
│   ├── config.py           # Настройки из .env (pydantic-settings)
│   ├── database.py         # Подключение к БД (async sessionmaker)
│   ├── models/             # SQLAlchemy модели
│   │   ├── __init__.py
│   │   ├── user.py         # User, Subscription
│   │   ├── product.py      # Product, Price, Store
│   │   └── search.py       # SearchHistory, SavedSearch
│   ├── schemas/            # Pydantic схемы (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── auth.py
│   │   └── subscription.py
│   ├── api/                # Эндпоинты (роутеры)
│   │   ├── __init__.py
│   │   ├── health.py       # Health check
│   │   ├── auth.py         # Регистрация, логин, JWT
│   │   ├── users.py        # Профиль, управление подпиской
│   │   ├── products.py     # Поиск, товары, цены
│   │   ├── stores.py       # Магазины
│   │   └── admin.py        # Админ-панель
│   ├── services/           # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── auth.py         # JWT, хеширование паролей
│   │   ├── search.py       # Поиск (точный + fuzzy)
│   │   ├── subscription.py # Проверка подписки, лимиты
│   │   ├── parser.py       # Управление парсерами
│   │   └── cache.py        # Redis-кэш
│   ├── parsers/            # Парсеры магазинов
│   │   ├── __init__.py
│   │   ├── base.py         # Базовый класс парсера
│   │   ├── tgssm.py        # Парсер ТГСМ
│   │   ├── profi.py        # Парсер Профи
│   │   ├── liberty.py      # Парсер Либерти
│   │   ├── greenspark.py   # Парсер Гринспарк
│   │   └── divizion.py     # Парсер Дивизион
│   └── utils/              # Вспомогательные функции
│       ├── __init__.py
│       └── text.py         # Нормализация текста, транслит
```

### 3.2 Модели данных (SQLAlchemy)

#### 3.2.1 User
```python
class User(Base):
    id: int (PK, autoincrement)
    email: str (unique, indexed)
    password_hash: str
    full_name: str
    phone: str | None
    company: str | None (название сервисного центра)
    is_active: bool (default=True)
    is_admin: bool (default=False)
    created_at: datetime
    updated_at: datetime
```

#### 3.2.2 Subscription
```python
class Subscription(Base):
    id: int (PK)
    user_id: int (FK -> User.id)
    plan: str (enum: "trial", "basic", "advanced")
    start_date: datetime
    end_date: datetime
    is_active: bool
    auto_renew: bool (default=True)
    created_at: datetime
```

#### 3.2.3 Store
```python
class Store(Base):
    id: int (PK)
    name: str          # "ТГСМ", "Профи", etc.
    slug: str          # "tgssm", "profi", etc.
    website_url: str   # URL магазина
    logo_url: str | None
    is_active: bool (default=True)
    created_at: datetime
```

#### 3.2.4 Product
```python
class Product(Base):
    id: int (PK)
    store_id: int (FK -> Store.id)
    external_id: str   # ID товара в магазине
    name: str
    normalized_name: str (для поиска)
    description: str | None
    image_url: str | None
    category: str | None
    price: Decimal
    old_price: Decimal | None
    currency: str (default="RUB")
    in_stock: bool (default=True)
    product_url: str   # Ссылка на товар в магазине
    last_updated: datetime
    created_at: datetime
```

#### 3.2.5 PriceHistory
```python
class PriceHistory(Base):
    id: int (PK)
    product_id: int (FK -> Product.id)
    price: Decimal
    recorded_at: datetime
```

#### 3.2.6 SearchHistory
```python
class SearchHistory(Base):
    id: int (PK)
    user_id: int (FK -> User.id)
    query: str
    filters: JSON | None
    results_count: int
    created_at: datetime
```

### 3.3 API Endpoints

#### 3.3.1 Аутентификация
| Method | Path | Описание | Доступ |
|--------|------|----------|--------|
| POST | `/api/auth/register` | Регистрация | Public |
| POST | `/api/auth/login` | Вход, выдаёт JWT | Public |
| POST | `/api/auth/refresh` | Обновление JWT | Public |
| POST | `/api/auth/logout` | Выход | Authenticated |

#### 3.3.2 Пользователи
| Method | Path | Описание | Доступ |
|--------|------|----------|--------|
| GET | `/api/users/me` | Профиль текущего пользователя | Authenticated |
| PATCH | `/api/users/me` | Обновление профиля | Authenticated |
| GET | `/api/users/me/subscription` | Текущая подписка | Authenticated |
| POST | `/api/users/me/subscription` | Оформление/смена подписки | Authenticated |
| DELETE | `/api/users/me/subscription` | Отмена подписки | Authenticated |
| GET | `/api/users/me/history` | История поиска | Authenticated |

#### 3.3.3 Товары и поиск
| Method | Path | Описание | Доступ |
|--------|------|----------|--------|
| GET | `/api/products` | Поиск товаров по запросу | Authenticated |
| GET | `/api/products/{id}` | Детальная информация о товаре | Authenticated |
| GET | `/api/products/{id}/price-history` | История цен товара | Authenticated |
| GET | `/api/stores` | Список магазинов | Public |
| GET | `/api/categories` | Список категорий | Public |

**Параметры поиска `GET /api/products`:**
- `q` — поисковый запрос (строка)
- `store` — фильтр по магазину (slug, опционально)
- `category` — фильтр по категории (опционально)
- `min_price`, `max_price` — фильтр по цене (опционально)
- `in_stock` — только в наличии (boolean, опционально)
- `sort_by` — сортировка: `price_asc` (default), `price_desc`, `date`
- `page`, `per_page` — пагинация (default: page=1, per_page=20)

**Логика поиска:**
1. Точное совпадение по `normalized_name`
2. Частичное совпадение (ILIKE / LIKE)
3. Для **продвинутого** тарифа — нечёткий поиск (fuzzy matching через триграммы `pg_trgm` или Levenshtein)

**Формат ответа:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "Дисплей iPhone 13",
      "store": { "name": "ТГСМ", "slug": "tgssm" },
      "price": 4500.00,
      "old_price": 5200.00,
      "image_url": "...",
      "in_stock": true,
      "product_url": "...",
      "is_cheapest": true
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

#### 3.3.4 Админ-панель
| Method | Path | Описание | Доступ |
|--------|------|----------|--------|
| GET | `/api/admin/users` | Список пользователей | Admin |
| GET | `/api/admin/users/{id}` | Детали пользователя | Admin |
| PATCH | `/api/admin/users/{id}` | Редактирование пользователя | Admin |
| DELETE | `/api/admin/users/{id}` | Блокировка пользователя | Admin |
| GET | `/api/admin/subscriptions` | Все подписки | Admin |
| GET | `/api/admin/parsers` | Статус парсеров | Admin |
| POST | `/api/admin/parsers/run` | Запуск парсера | Admin |
| GET | `/api/admin/stats` | Статистика системы | Admin |

### 3.4 Система парсинга

#### 3.4.1 Архитектура парсера
```
Базовый класс Parser (base.py)
├── TGSM_Parser
├── Profi_Parser
├── Liberty_Parser
├── GreenSpark_Parser
└── Divizion_Parser
```

Каждый парсер реализует интерфейс:
```python
class Parser(ABC):
    @abstractmethod
    async def parse_product(self, url: str) -> ProductData: ...
    @abstractmethod
    async def search(self, query: str) -> list[ProductData]: ...
    @abstractmethod
    async def update_catalog(self) -> list[ProductData]: ...
```

#### 3.4.2 Расписание
- Парсинг каталога: ежедневно (ночью, в 03:00)
- Обновление цен: каждые 6 часов для всех тарифов
- Приоритетные обновления для популярных товаров

#### 3.4.3 Хранение данных
- Товары и цены — PostgreSQL
- Кэш результатов поиска — Redis (TTL 5 минут)
- Очередь задач парсинга — Redis (через RQ / arq)

### 3.5 Права доступа по тарифам

| Функция | Пробный (7 дн.) | Базовый (399 ₽/мес) | Продвинутый (499 ₽/мес) |
|---------|---------|---------|------------|
| Магазины | 5 | 5 | 5 |
| Мониторинг товаров | до 10 | до 100 | до 500 |
| Умный поиск (fuzzy) | — | — | ✓ |
| Уведомления о снижении цен | — | — | ✓ |
| Экспорт отчётов | — | — | ✓ |
| Поддержка | — | рабочие часы | 24/7 |

**Скидка при первой оплате:** 20% на любой платный тариф.

### 3.6 Fuzzy Search (нечёткий поиск)

Реализация для продвинутого тарифа:
- Расширение PostgreSQL `pg_trgm` (триграммы)
- Индекс GiST на `normalized_name`
- Алгоритм: `similarity()` + `levenshtein()` через plpython или на уровне Python
- Транслитерация для поиска на русском при латинской раскладке
- Автодополнение (autocomplete) через триграммы
- Исправление опечаток (1-2 символа)

---

## 4. Frontend

### 4.1 Структура проекта (FSD)

```
frontend/src/
├── index.tsx                          # Точка входа
├── app/
│   ├── App.tsx                        # Корневой компонент
│   └── App.module.scss
├── pages/
│   ├── home/
│   │   └── ui/
│   │       └── Home.tsx               # Главная (лендинг)
│   ├── search/
│   │   └── ui/
│   │       └── Search.tsx             # Страница поиска (TODO)
│   ├── account/
│   │   └── ui/
│   │       └── Account.tsx            # Личный кабинет (TODO)
│   └── admin/
│       └── ui/
│           └── Admin.tsx              # Админ-панель (TODO)
├── widgets/
│   ├── Header/                        # Шапка сайта
│   │   └── ui/
│   │       ├── Header.tsx
│   │       └── Header.module.scss
│   ├── Footer/                        # Подвал
│   │   └── ui/
│   │       ├── Footer.tsx
│   │       └── Footer.module.scss
│   ├── homeWidget/                    # Виджет главной страницы
│   │   └── ui/
│   │       ├── index.tsx
│   │       ├── Hero/
│   │       ├── Carousel/
│   │       ├── Advantages/
│   │       ├── Dashboard/
│   │       ├── Prices/
│   │       └── BannerAccount/
│   ├── searchWidget/                  # Поиск (TODO)
│   │   └── ui/
│   │       ├── SearchBar.tsx
│   │       ├── SearchResults.tsx
│   │       └── ProductCard.tsx
│   └── authWidget/                    # Аутентификация (TODO)
│       └── ui/
│           ├── LoginForm.tsx
│           └── RegisterForm.tsx
├── features/
│   ├── auth/                          # Фича аутентификации (TODO)
│   ├── subscription/                  # Фича подписки (TODO)
│   └── search/                        # Фича поиска (TODO)
├── entities/
│   ├── user/                          # Сущность пользователя (TODO)
│   ├── product/                       # Сущность товара (TODO)
│   └── store/                         # Сущность магазина (TODO)
└── shared/
    ├── assets/
    │   └── images/                    # Статические изображения
    ├── styles/
    │   └── index.css                  # Глобальные стили
    └── ui/
        └── IconSVG.tsx                # SVG-иконки
```

### 4.2 Роутинг (react-router-dom v7)

| Path | Page | Описание |
|------|------|----------|
| `/` | Home | Лендинг (неавторизованным / авторизованным) |
| `/search` | Search | Страница поиска товаров |
| `/search?q=...` | Search | Поиск с параметром запроса |
| `/product/:id` | Product | Детальная страница товара |
| `/account` | Account | Личный кабинет |
| `/account/subscription` | Subscription | Управление подпиской |
| `/account/history` | SearchHistory | История поиска |
| `/login` | Login | Вход |
| `/register` | Register | Регистрация |
| `/admin` | Admin | Админ-панель |
| `/faq` | FAQ | Часто задаваемые вопросы |
| `/contacts` | Contacts | Контакты |
| `/pricing` | Pricing | Тарифы |
| `/privacy` | Privacy | Политика конфиденциальности |
| `/terms` | Terms | Условия использования |

### 4.3 Состояние и данные

- **Глобальное состояние:** React Context + useReducer (на начальном этапе)
- **Запросы к API:** fetch (стандартный) или axios
- **Аутентификация:** JWT токен в localStorage, контекст AuthContext
- **Темы:** Только светлая тема (MVP)

### 4.4 Требования к вёрстке

- Адаптивная вёрстка (desktop first, mobile-friendly)
- SCSS Modules для изоляции стилей
- Поддержка Chrome, Firefox, Safari (2 последние версии)
- Шрифт: Raleway (основной), DM Sans / Lexend / Montserrat (дополнительные)

### 4.5 Компоненты (текущее состояние)

#### Header
- Логотип BScout
- Навигация: Tables, Contacts, FAQ
- Иконки: Личный кабинет, Поддержка
- Адаптивное меню (бургер)

#### Footer
- Логотип + теглайн
- Колонки ссылок: Product, Company, Legal
- Социальные сети: Telegram, VK
- Контакты: телефон, email

#### HomeWidget (композиция)
1. **Hero** — заголовок, описание, CTA кнопки, декоративные изображения
2. **Carousel** — бесконечная карусель логотипов магазинов-партнёров
3. **Advantages** — три блока преимуществ (актуальность, гибкость, экономия времени)
4. **Dashboard** — превью дашборда со скриншотом
5. **Prices** — три тарифа (Пробный/Базовый/Продвинутый)
6. **BannerAccount** — финальный CTA-баннер

### 4.6 Планируемые страницы (после MVP)

#### SearchPage
- Поисковая строка с автодополнением
- Фильтры: магазин, категория, цена, наличие
- Результаты: карточки товаров с ценой, магазином, выделением самого дешёвого
- Пагинация / бесконечная прокрутка

#### ProductPage
- Фото товара
- Название, описание, категория
- Таблица цен по магазинам
- График истории цены
- Ссылка на магазин

#### AccountPage
- Информация о пользователе
- Текущий тариф и дата окончания
- История поиска
- Недавно просмотренные товары
- Кнопка отмены/смены подписки

#### AdminPage
- Дашборд со статистикой
- Управление пользователями
- Управление подписками
- Управление парсерами (запуск, статус, логи)
- Управление магазинами

---

## 5. Аутентификация и авторизация

### 5.1 Механизм
- JWT (access token + refresh token)
- Access token: 15 минут
- Refresh token: 30 дней (в httpOnly cookie)
- Пароли хешируются через bcrypt (passlib)

### 5.2 Flow регистрации
1. Пользователь заполняет форму (email, пароль, имя, телефон)
2. POST `/api/auth/register` — создаётся пользователь + подписка trial на 7 дней
3. Автоматический вход (выдача JWT)
4. Редирект на `/search`

### 5.3 Flow логина
1. POST `/api/auth/login` с email + password
2. Выдача access + refresh token
3. Редирект на `/search` (или предыдущую страницу)

### 5.4 Middleware
- Проверка JWT на всех маршрутах, кроме `/api/auth/*`, `/api/health`, `/api/stores`, `/api/categories`
- Проверка тарифа на маршрутах поиска
- Проверка роли admin на `/api/admin/*`

---

## 6. Docker

### 6.1 docker-compose.yml (dev)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ../backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    env_file: ../backend/.env

  frontend:
    build: ../frontend
    ports: ["3000:3000"]
    depends_on: [backend]
```

### 6.2 Dockerfile.backend
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.3 Dockerfile.frontend
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

---

## 7. Этапы разработки

### Этап 1. MVP (текущий статус — завершён)
- [x] FSD-структура фронтенда
- [x] Лендинг (Home: Header + Hero + Carousel + Advantages + Dashboard + Prices + BannerAccount + Footer)
- [x] Backend skeleton (FastAPI + health endpoint)
- [x] Docker (PostgreSQL + Redis)
- [x] Сборка frontend (npm run build — успешно)

### Этап 2. Backend API
- [ ] Модели данных (SQLAlchemy)
- [ ] Миграции (Alembic)
- [ ] API: аутентификация (register, login, JWT)
- [ ] API: пользователи, подписки
- [ ] API: товары, поиск (точное + частичное совпадение)
- [ ] API: админ-панель
- [ ] Dockerfile для backend

### Этап 3. Парсинг
- [ ] Базовый класс парсера
- [ ] Парсеры для 5 магазинов (ТГСМ, Профи, Либерти, Гринспарк, Дивизион)
- [ ] Расписание парсинга
- [ ] Кэширование результатов

### Этап 4. Frontend — страницы
- [ ] Страница поиска (SearchBar, SearchResults, ProductCard)
- [ ] Страница товара (детали, история цен, сравнение)
- [ ] Личный кабинет (профиль, подписка, история)
- [ ] Страницы логина / регистрации
- [ ] Админ-панель

### Этап 5. Интеграция
- [ ] Подключение frontend к API
- [ ] Защита маршрутов (AuthGuard, SubscriptionGuard)
- [ ] Обработка ошибок, уведомления
- [ ] Общая аутентификация (login/register flow end-to-end)

### Этап 6. Premium-фичи
- [ ] Нечёткий поиск (pg_trgm, триграммы)
- [ ] Автодополнение (autocomplete)

### Этап 7. Production
- [ ] Docker Compose (full stack)
- [ ] Nginx конфигурация
- [ ] CI/CD (GitHub Actions)
- [ ] Мониторинг и логирование

---

## 8. Требования к безопасности

- JWT токены с ограниченным сроком жизни
- Refresh token в httpOnly cookie (защита от XSS)
- CORS — только разрешённые origins
- SQL-инъекции — предотвращаются через SQLAlchemy ORM
- XSS — защита через React (автоматическое экранирование)
- Rate limiting на endpointы аутентификации
- Пароли — только в хешированном виде (bcrypt)
- .env — не в репозитории (в .gitignore)
- Все запросы к API — через HTTPS (в production)

---

## 9. Мониторинг и логирование (перспектива)

- Structured logging (python logging + JSON)
- Health check endpoint (`/api/health`)
- Метрики парсинга (количество товаров, успешность)
- Метрики пользователей (регистрации, подписки, поиски)

---

## 10. Примечания

- Все цены указаны в рублях (₽)
- Валютный формат: XXXX.XX (2 знака после запятой)
- Даты: ISO 8601 (YYYY-MM-DDTHH:mm:ss)
- Язык интерфейса: русский (MVP)
- favicon: logo1.webp
