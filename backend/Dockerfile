# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Стадия сборки: здесь и только здесь живут компилятор и заголовочные файлы.
# Всё, для чего pip не нашёл готового колеса, собирается тут; в финальный
# образ переезжает только готовый /opt/venv — build-essential в него не попадает.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# ---------------------------------------------------------------------------
# Финальный образ: интерпретатор + готовое виртуальное окружение, без тулчейна.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# FORWARDED_ALLOW_IPS читает сам uvicorn. Без неё X-Forwarded-* принимаются
# только от 127.0.0.1, и за nginx реальный IP клиента теряется (а rate limit
# начинает считать всех пользователей за одного). В проде значение стоит сузить
# до подсети docker-сети edge — см. .env.prod.example.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    APP_PORT=8000 \
    UVICORN_WORKERS=2 \
    FORWARDED_ALLOW_IPS="*"

# Непривилегированный пользователь: процесс приложения не должен быть root.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY --chown=app:app alembic.ini ./alembic.ini
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app src ./src
COPY --chown=app:app data ./data

USER app

EXPOSE 8000

# Проверка живости через штатный /api/health, без установки curl/wget в образ.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os,sys,urllib.request; p=os.environ.get('APP_PORT','8000'); sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+p+'/api/health', timeout=3).status==200 else 1)"]

# ВАЖНО: миграции здесь НЕ запускаются.
# Раньше CMD был `alembic upgrade head && uvicorn ...`: при нескольких репликах
# они стартовали одновременно и дрались за блокировку таблицы alembic_version.
# Теперь миграции — отдельный шаг:
#     docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm migrate
# либо сервис migrate поднимается сам и backend/worker ждут его завершения.
CMD ["sh", "-c", "exec uvicorn src.main:app --host 0.0.0.0 --port ${APP_PORT} --workers ${UVICORN_WORKERS} --proxy-headers --no-server-header"]
