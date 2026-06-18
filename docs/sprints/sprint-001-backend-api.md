# Спринт 1 — Backend API

**Период:** 14 дней
**Цель:** Разработать полный набор backend API для BScout: модели данных, миграции, аутентификация, пользователи, товары, поиск, админ-панель.

---

## Задачи

### 1.1 Настройка окружения и инфраструктура (день 1)

- [ ] Создать `src/config.py` — pydantic-settings (DATABASE_URL, REDIS_URL, SECRET_KEY, etc.)
- [ ] Создать `src/database.py` — async engine + sessionmaker
- [ ] Создать `.env` из `.env.example` с реальными данными
- [ ] Настроить Alembic (`alembic init alembic`, `alembic.ini`)
- [ ] Проверить подключение к PostgreSQL через Docker

**Риски:** Отсутствие Docker на машине разработчика. Resolver: использовать SQLite для локальной разработки.

### 1.2 Модели данных SQLAlchemy (дни 2-3)

- [ ] `src/models/__init__.py`
- [ ] `src/models/user.py` — User, Subscription
- [ ] `src/models/product.py` — Store, Product, PriceHistory
- [ ] `src/models/search.py` — SearchHistory
- [ ] Сгенерировать и применить первую миграцию (`alembic revision --autogenerate`)
- [ ] Добавить индексы (email, normalized_name, store_id, external_id)

**Важно:**
- `Subscription.plan` — enum: `"trial"`, `"basic"`, `"advanced"`
- `Product.normalized_name` — для поиска (нижний регистр, без спецсимволов)
- `User.password_hash` — хранить только bcrypt-хеш

### 1.3 Аутентификация и JWT (дни 4-6)

- [ ] `src/services/auth.py` — хеширование (passlib bcrypt), создание/верификация JWT
- [ ] `src/schemas/auth.py` — RegisterRequest, LoginRequest, TokenResponse
- [ ] `src/api/auth.py`:
  - `POST /api/auth/register` — создать пользователя + триал на 10 дней
  - `POST /api/auth/login` — выдать access + refresh token
  - `POST /api/auth/refresh` — обновить access token
  - `POST /api/auth/logout` — инвалидировать refresh token
- [ ] Middleware: JWTBearer (проверка access token на защищённых маршрутах)

**Детали:**
- Access token: 15 минут
- Refresh token: 30 дней (в httpOnly cookie, без хранения в БД — или Redis blacklist)
- При регистрации автоматически создаётся Subscription trial на 10 дней

### 1.4 Пользователи и подписки (дни 7-8)

- [ ] `src/schemas/user.py` — UserResponse, UserUpdate, SubscriptionResponse
- [ ] `src/schemas/subscription.py` — SubscriptionCreate, SubscriptionUpdate
- [ ] `src/api/users.py`:
  - `GET /api/users/me` — профиль
  - `PATCH /api/users/me` — обновление профиля
  - `GET /api/users/me/subscription` — текущая подписка
  - `POST /api/users/me/subscription` — оформить/сменить подписку
  - `DELETE /api/users/me/subscription` — отменить подписку
  - `GET /api/users/me/history` — история поиска
- [ ] `src/services/subscription.py` — проверка лимитов (is_active, end_date, plan)

### 1.5 Товары и поиск (дни 9-11)

- [ ] `src/schemas/product.py` — ProductResponse, ProductDetailResponse, SearchResponse, StoreResponse
- [ ] `src/api/products.py`:
  - `GET /api/products?q=...&store=...&page=...` — поиск с фильтрацией и пагинацией
  - `GET /api/products/{id}` — детальная информация
  - `GET /api/products/{id}/price-history` — история цен
- [ ] `src/api/stores.py`: `GET /api/stores` — список магазинов
- [ ] `src/services/search.py`:
  - Точное совпадение по `normalized_name`
  - Частичное совпадение (ILIKE)
  - Для advanced-тарифа: fuzzy match (pg_trgm)
- [ ] `src/services/cache.py` — кэширование результатов поиска в Redis (TTL 5 мин)

**Параметры поиска:**
- `q` — запрос (строка)
- `store` — фильтр по магазину (slug)
- `category` — фильтр по категории
- `min_price`, `max_price` — фильтр по цене
- `in_stock` — только в наличии
- `sort_by` — `price_asc` (default), `price_desc`, `date`
- `page`, `per_page` — пагинация (default: 1, 20)

### 1.6 Админ-панель (дни 12-13)

- [ ] `src/api/admin.py`:
  - `GET /api/admin/users` — список пользователей (с пагинацией)
  - `GET /api/admin/users/{id}` — детали пользователя
  - `PATCH /api/admin/users/{id}` — редактирование
  - `DELETE /api/admin/users/{id}` — блокировка (is_active=false)
  - `GET /api/admin/subscriptions` — все подписки
  - `GET /api/admin/stats` — статистика системы
- [ ] Middleware: проверка роли `is_admin=True`
- [ ] Эндпоинты для парсеров (заглушки):
  - `GET /api/admin/parsers` — статус
  - `POST /api/admin/parsers/run` — запуск

### 1.7 Dockerfile и финализация (день 14)

- [ ] Создать `Dockerfile` для backend (python:3.11-slim + uvicorn)
- [ ] Обновить `docker-compose.yml` — добавить сервис backend
- [ ] Протестировать все эндпоинты (curl / httpx)
- [ ] Написать документацию для API (docstrings в роутерах)
- [ ] Проверить линтером (ruff / flake8)

---

## Критерии готовности (Definition of Done)

- [ ] Все модели SQLAlchemy созданы и мигрированы (alembic upgrade head — успешно)
- [ ] Регистрация + логин работают end-to-end (JWT выдача)
- [ ] Поиск товаров возвращает корректные результаты (точное + частичное совпадение)
- [ ] Подписки создаются при регистрации (trial 10 дней)
- [ ] Админ-эндпоинты доступны только с ролью admin
- [ ] Dockerfile собирается (`docker build -t bscout-backend .`)
- [ ] docker-compose поднимает всё вместе (postgres + redis + backend)
- [ ] Код покрыт type hints
- [ ] Все зависимости зафиксированы в requirements.txt

---

# Спринт 2 — Парсинг магазинов

**Период:** 10 дней
**Цель:** Разработать систему модульных парсеров для 5 магазинов (ТГСМ, Профи, Либерти, Гринспарк, Дивизион) с кэшированием, расписанием и админ-контролем.

---

## Задачи

### 2.1 Базовый класс парсера (день 1)

- [ ] `src/parsers/__init__.py`
- [ ] `src/parsers/base.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

@dataclass
class ProductData:
    external_id: str
    name: str
    price: Decimal
    old_price: Decimal | None = None
    currency: str = "RUB"
    in_stock: bool = True
    category: str | None = None
    description: str | None = None
    image_url: str | None = None
    product_url: str | None = None
    normalized_name: str = ""

class Parser(ABC):
    store_slug: str = ""
    store_name: str = ""

    @abstractmethod
    async def search(self, query: str) -> list[ProductData]: ...

    @abstractmethod
    async def parse_product(self, url: str) -> ProductData | None: ...

    @abstractmethod
    async def update_catalog(self) -> list[ProductData]: ...
```

- [ ] `src/parsers/exceptions.py`:
  - `ParserError` — базовое исключение парсера
  - `ParserConnectionError` — ошибка подключения к магазину
  - `ParserParseError` — ошибка парсинга HTML/JSON
  - `ParserAuthError` — ошибка авторизации на сайте магазина
- [ ] `src/parsers/utils.py`:
  - `normalize_name(name: str) -> str` — нижний регистр, удаление спецсимволов, лишних пробелов
  - `parse_price(text: str) -> Decimal` — извлечение числа из строки "4 500 ₽"
  - `safe_request(url, headers, timeout, retries)` — обёртка над httpx с повторными попытками
  - `compare_products(a: ProductData, b: ProductData) -> bool` — сравнение товаров по external_id и цене

**Детали:**
- Все парсеры — асинхронные (httpx.AsyncClient)
- Timeout на запрос: 15 секунд
- Количество повторов при ошибке: 3 (с exponential backoff)
- User-Agent: рандомизированный (ротация 5+ вариантов)
- Поддержка прокси (опционально, из config)

### 2.2 Парсер ТГСМ (day 2)

- [ ] `src/parsers/tgssm.py`

**Источник:** https://taggsm.ru

**Метод:** Парсинг HTML через BeautifulSoup / lxml.

**Структура сайта:**
- Каталог: `/catalog/` → список категорий
- Категория: `/catalog/{category_slug}/` → список товаров (пагинация)
- Товар: `/product/{id}/` — название, цена, фото, описание, наличие
- Поиск: `/search/?q={query}` — результаты поиска

**Детали реализации:**
- Определить CSS-селекторы для:
  - Название товара (h1/page_title)
  - Цена (текущая + старая)
  - Изображение (src первого изображения)
  - Описание (div.description / article)
  - Наличие (stock status badge)
  - Пагинация (next page link)
- `search(query)`: GET `/search/?q={query}`, распарсить список результатов
- `parse_product(url)`: GET url товара, извлечь все поля
- `update_catalog()`: обойти категории → страницы → товары

**Риски:** Изменение HTML-структуры сайта. Решение: вынести селекторы в конфиг парсера.

### 2.3 Парсер Профи (день 2-3)

- [ ] `src/parsers/profi.py`

**Источник:** https://siriust.ru

**Метод:** Анализ сетевых запросов (HTML + XHR). Если есть JSON API — использовать его.

**План:**
1. Открыть DevTools → Network → найти XHR-запросы при поиске
2. Если есть GraphQL/REST API endpoint — парсить через него
3. Иначе — HTML парсинг (аналогично ТГСМ)

**Поля для извлечения:**
- Название, цена, старая цена, изображение, описание, наличие, категория, URL товара

### 2.4 Парсер Либерти (день 3-4)

- [ ] `src/parsers/liberty.py`

**Источник:** https://liberti.ru

**Метод:** Аналогично — сначала проверить JSON API, иначе HTML.

**Особенности:**
- Определить тип сайта (интернет-магазин на CMS или самописный)
- Если на TypeCommerce / 1C-Bitrix — могут быть стандартные REST-ручки
- Найти sitemap.xml для структуры каталога

### 2.5 Парсер Гринспарк (день 4-5)

- [ ] `src/parsers/greenspark.py`

**Источник:** https://green-spark.ru

**Метод:** HTML парсинг (аналогично ТГСМ).

**Поиск:** Анализ формы поиска — GET или POST, параметры запроса.

### 2.6 Парсер Дивизион (день 5-6)

- [ ] `src/parsers/divizion.py`

**Источник:** https://divizion126.ru

**Метод:** HTML парсинг.

**Особенности:**
- Меньший каталог — потенциально проще для парсинга
- Все поля стандартные (название, цена, фото)

### 2.7 Сервис управления парсерами (день 6-7)

- [ ] `src/services/parser.py`:

```python
class ParserService:
    _parsers: dict[str, Parser] = {}  # slug -> instance

    def register(self, parser: Parser): ...
    def get(self, slug: str) -> Parser | None: ...
    def list_parsers(self) -> list[ParserInfo]: ...
    async def run_all(self) -> dict[str, ParseResult]: ...
    async def run_one(self, slug: str) -> ParseResult: ...
```

- [ ] `src/schemas/parser.py`:
  - `ParserInfo` — slug, name, status (idle/running/error), last_run, products_count
  - `ParseResult` — slug, status, products_added, products_updated, errors, duration_sec
- [ ] `src/models/product.py` — добавить поля (если нужно):
  - `last_parsed_at: datetime | None` — время последнего парсинга

**Логика работы:**
1. `run_all()` — запускает все парсеры параллельно (asyncio.gather)
2. Каждый парсер возвращает `list[ProductData]`
3. Для каждого товара: upsert в БД (по `store_id + external_id`)
4. Если цена изменилась — запись в PriceHistory
5. Результаты сохраняются в Redis (для быстрого доступа из админки)

### 2.8 Расписание и очередь (день 7-8)

- [ ] `src/services/scheduler.py`:

```python
class ParserScheduler:
    async def schedule_catalog_update(self): ...  # ежедневно в 03:00
    async def schedule_price_update(self, interval: str): ...  # каждые N часов
    async def schedule_priority_update(self, product_ids: list[int]): ...
```

**Архитектура:**
- **Вариант A (рекомендуемый):** Redis + arq (async RQ)
  - `arq` — лёгкая очередь задач на Redis, поддерживает async
  - Создать `src/worker.py` — воркер arq, который запускает парсеры по расписанию
  - Cron-задачи: `catalog_update(day, "03:00")`, `price_update(hour, */6)`
- **Вариант B (fallback):** BackgroundTasks в FastAPI + asyncio.create_task
  - Только для MVP, не подходит для production (нет persistence)

**Расписание по умолчанию:**
- Полный парсинг каталога: каждый день в 03:00 ночи
- Обновление цен: каждые 6 часов (для базового тарифа)
- Приоритетные товары (часто ищут): обновление раз в час

### 2.9 Кэширование (день 8-9)

- [ ] `src/services/cache.py` (расширение):

```python
class CacheService:
    async def get_search_results(self, query: str, filters: dict) -> list[ProductData] | None: ...
    async def set_search_results(self, query: str, filters: dict, results: list[ProductData], ttl: int = 300): ...
    async def invalidate_product(self, product_id: int): ...
    async def get_parser_status(self, slug: str) -> ParserInfo | None: ...
    async def set_parser_status(self, slug: str, status: ParserInfo, ttl: int = 3600): ...
```

**Ключи Redis:**
- `search:{md5(query+sort+page)}` → JSON (TTL 5 мин)
- `parser:status:{slug}` → JSON (TTL 1 час)
- `product:{id}` → JSON (TTL 15 мин)
- `parser:lock:{slug}` — блокировка для предотвращения параллельного запуска (TTL = время выполнения)

### 2.10 Админ-эндпоинты для парсеров (день 9-10)

- [ ] `src/api/admin.py` — замена заглушек на реальную логику:

```python
@router.get("/api/admin/parsers", tags=["admin"])
async def get_parsers_status(admin=Depends(admin_required)):
    """Статус всех парсеров: запущен/остановлен, время последнего запуска, кол-во товаров."""
    ...

@router.post("/api/admin/parsers/run", tags=["admin"])
async def run_parser(
    slug: str | None = Body(None),  # None = все
    admin=Depends(admin_required),
):
    """Запустить парсер (один или все). Возвращает результат."""
    ...

@router.get("/api/admin/parsers/logs/{slug}", tags=["admin"])
async def get_parser_logs(slug: str, admin=Depends(admin_required)):
    """Последние N логов парсера (из Redis или файла)."""
    ...

@router.post("/api/admin/parsers/{slug}/priority", tags=["admin"])
async def add_priority_product(
    slug: str,
    product_url: str = Body(...),
    admin=Depends(admin_required),
):
    """Добавить товар в приоритетное обновление."""
    ...
```

- [ ] `src/models/parser_log.py` (опционально, для постоянного хранения логов):
  - id, slug, status, products_count, errors_count, started_at, finished_at, duration_ms

**UI в админке (задел на будущее):**
- Таблица парсеров: колонки "Магазин", "Статус", "Товаров", "Последний запуск", "Действия"
- Кнопки "Запустить", "Логи", "Настроить расписание"
- Статус: 🟢 работает / 🟡 в процессе / 🔴 ошибка

---

## Тестирование парсеров (cross-cutting)

- [ ] `tests/parsers/test_base.py` — тесты базового класса и утилит
- [ ] `tests/parsers/test_tgssm.py` — тест поиска + парсинга товара
- [ ] `tests/parsers/test_profi.py` — тест поиска + парсинга товара
- [ ] `tests/parsers/test_liberty.py`
- [ ] `tests/parsers/test_greenspark.py`
- [ ] `tests/parsers/test_divizion.py`
- [ ] `tests/parsers/test_parser_service.py` — upsert товаров, запись истории цен
- [ ] `tests/parsers/test_scheduler.py` — расписание, блокировки

**Типы тестов:**
- **Unit-тесты:** нормализация названий, парсинг цен, сравнение товаров
- **Integration-тесты:** парсинг реальной страницы товара (с моками httpx)
- **Fixture:** сохранённые HTML-страницы магазинов в `tests/fixtures/html/`

---

## Критерии готовности парсинга

- [ ] Все 5 парсеров реализованы и протестированы
- [ ] `ParserService.run_all()` — успешно парсит все магазины и сохраняет в БД
- [ ] Цены обновляются (upsert), изменения записываются в PriceHistory
- [ ] Redis-кэш работает: поиск и статусы парсеров
- [ ] Админ-эндпоинты возвращают статус и логи
- [ ] Расписание настроено (arq worker)
- [ ] Блокировка двойного запуска работает (parser:lock)
- [ ] Обработка ошибок: при падении одного парсера остальные продолжают работу

---

## Зависимости

- **Добавить в requirements.txt:**
  - `httpx` — async HTTP-клиент
  - `beautifulsoup4` + `lxml` — парсинг HTML
  - `arq` — очередь задач на Redis
  - `tenacity` — retry логика
- **Блокирует:** Этап 4 (фронтенд с реальными данными), Этап 5 (интеграция)
- **Зависит от:** Этап 2 (модели Product, Store, PriceHistory в БД)

## Оценка

| Задача | Дни | Кто |
|--------|-----|-----|
| Базовый класс + утилиты | 1 | — |
| Парсер ТГСМ | 1 | — |
| Парсер Профи | 1 | — |
| Парсер Либерти | 1 | — |
| Парсер Гринспарк | 1 | — |
| Парсер Дивизион | 1 | — |
| ParserService + upsert | 1 | — |
| Расписание + arq worker | 2 | — |
| Кэширование | 1 | — |
| Админ-эндпоинты + тесты | 2 | — |
| **Итого** | **12** | — |
