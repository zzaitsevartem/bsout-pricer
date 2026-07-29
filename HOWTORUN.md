# HOWTORUN — BScout Pricer

> Проверенные инструкции: установка → запуск → тесты

---

## 1. Требования

| Компонент | Версия |
|-----------|--------|
| Docker Desktop | latest |
| Python | 3.11+ |
| Node.js | 18+ |
| pnpm | 10+ (или npm 9+) |

Проверить:

```bash
docker --version && python3 --version && node --version && pnpm --version
```

---

## 2. База данных (Docker)

```bash
# Запустить PostgreSQL 16 + Redis 7
docker compose up -d

# Проверить что контейнеры запущены
docker ps
# Должны быть: bscout-postgres (5432), bscout-redis (6379)
```

---

## 3. Backend (FastAPI)

### 3.1 Установка зависимостей

```bash
cd backend

# Создать виртуальное окружение (если нет)
python3 -m venv .venv

# Активировать
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# bcrypt: зафиксировать версию (passlib совместим с 4.x)
pip install 'bcrypt==4.0.1'
```

### 3.2 Настройка .env

```bash
cp .env.example .env
```

По умолчанию `.env` настроен на:
- `localhost:5432` (PostgreSQL, БД `bscout`, пользователь `bscout`)
- `localhost:6379` (Redis)

### 3.3 Миграции

```bash
alembic upgrade head
```

Ожидаемый вывод:
```
INFO  [alembic.runtime.migration] Running upgrade  -> b8a3e09670ae
INFO  [alembic.runtime.migration] Running upgrade b8a3e09670ae -> 9c7d8e2f1a3b
```

### 3.4 Seed-данные

```bash
python -m src.seed
```

Создаёт:
- **Пользователи:** `admin@bscout.ru / admin123` (админ, advanced-подписка), `user@bscout.ru / user123` (basic-подписка)
- **Магазины:** Ozon, Wildberries, Яндекс Маркет, DNS, М.Видео
- **Категории:** Смартфоны, Ноутбуки, Наушники, Игровые консоли, Умные часы
- **Товары:** 10 тестовых товаров с историей цен (60 записей)

### 3.5 Запуск

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

API доступно:
- http://localhost:8000/api/health
- http://localhost:8000/docs (Swagger)
- http://localhost:8000/redoc (ReDoc)

---

## 4. Frontend (Next.js 14)

### 4.1 Установка зависимостей

```bash
cd frontend

# pnpm (рекомендуется)
pnpm install

# или npm
npm install
```

### 4.2 Запуск dev-сервера

```bash
pnpm dev
# или: npm run dev
```

Фронтенд на http://localhost:3000

Прокси работает автоматически:
- `/api/*` на фронте → `http://localhost:8000/api/*` (настройка в `next.config.mjs`)

### 4.3 Сборка и линтинг

```bash
pnpm build    # Production-сборка (0 ошибок)
pnpm lint     # ESLint + TypeScript check
```

---

## 5. Тесты

### 5.1 Backend-тесты (pytest)

```bash
cd backend

# Внутри .venv:
# pytest не установлен в .venv, используйте отдельный:
/tmp/venv-bscout/bin/pytest tests/ -v

# Или установите pytest и зависимости:
pip install pytest pytest-asyncio aiosqlite
pytest tests/ -v
```

Тесты используют:
- **SQLite** (aiosqlite) — изолированная БД на каждый тест
- **Mock Redis** — все вызовы к Redis заменены AsyncMock
- **Фикстуры:** `setup_db` (create_all/drop_all), `db_session`, `client` (httpx.AsyncClient)

**19 тестов** — все должны проходить:
- `test_auth.py` — 8 тестов (register, login, refresh, logout)
- `test_health.py` — 1 тест
- `test_plans.py` — 3 теста (list, fields, slugs)
- `test_users.py` — 7 тестов (me, update, subscription)

### 5.2 Frontend-сборка

```bash
cd frontend
pnpm build    # Production-сборка
pnpm lint     # Линтинг
```

Frontend-тестов (jest/playwright) пока нет.

---

## 6. Быстрая проверка API

```bash
# Health
curl http://localhost:8000/api/health

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@bscout.ru","password":"admin123"}'

# Plans (публичный)
curl http://localhost:8000/api/plans

# Сохранить токен
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@bscout.ru","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Профиль
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN"

# Подписка
curl http://localhost:8000/api/users/me/subscription \
  -H "Authorization: Bearer $TOKEN"

# Товары
curl "http://localhost:8000/api/products?limit=3" \
  -H "Authorization: Bearer $TOKEN"

# История цен
curl "http://localhost:8000/api/products/1/price-history" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 7. Известные проблемы

| Проблема | Решение |
|----------|---------|
| Docker порты заняты | `docker stop learn-postgres learn-redis learn-minio` |
| `ModuleNotFoundError: email_validator` | `pip install email-validator` |
| `ValueError: password cannot be longer than 72 bytes` | `pip install 'bcrypt==4.0.1'` |
| `MissingGreenlet` в тестах | Убедиться что `pip install greenlet` и `db.refresh()` после flush |

---

## 8. Credentials для тестирования

| Роль | Email | Пароль |
|------|-------|--------|
| **Администратор** | `admin@bscout.ru` | `admin123` |
| **Обычный пользователь** | `user@bscout.ru` | `user123` |

---

## 9. Команды одной строкой

```bash
# Полный запуск (из корня проекта):
docker compose up -d
cd backend && .venv/bin/alembic upgrade head && .venv/bin/python -m src.seed
nohup .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/bscout-backend.log 2>&1 &
cd ../frontend && pnpm dev
```
