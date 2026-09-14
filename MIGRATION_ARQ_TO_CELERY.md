# Миграция очереди задач: ARQ → Celery + Flower

Отчёт по переводу фоновых задач проекта с `arq` на `celery[redis]` с мониторингом
через Flower. Все изменённые компоненты перечислены ниже и отмечены по факту
выполнения.

## Итог

Миграция завершена. Бэкенд: **1060 тестов зелёные** (385 unit + 675 integration),
ruff чист. Docker-окружение: worker/beat/flower собраны и подняты (`healthy`).
E2E-проверка: задача, поставленная из хоста, выполнена docker-воркером
(`cleanup_refresh_tokens` → `succeeded {'deleted': 3}`), Flower показывает её
в `/api/tasks`. Flower доступен на `http://localhost:5555`.

## Чек-лист изменённых компонентов

### Зависимости
- [x] `backend/requirements.txt`: `arq==0.28.0` → `celery[redis]==5.6.3` + `flower==2.1.0`
- [x] `backend/pyproject.toml`: `arq = "^0.28.0"` → celery/flower
- [x] arq удалён из venv (`pip uninstall arq`)

### Новый модуль приложения Celery
- [x] `backend/src/celery_app.py` — приложение, настройки (UTC, broker/backend =
      `settings.redis_url`, `task_events`, `task_track_started`, `task_ignore_result`),
      `beat_schedule` (5 расписаний вместо arq cron)

### Воркер
- [x] `backend/src/worker.py` — 8 задач на `@celery_app.task`
      (run_parser, sync_catalog, sync_prices, expire_subscriptions,
      cleanup_refresh_tokens, send_password_mail, send_broadcast, prune_history);
      async-ядра для тестов (`_sync_catalog`, `_expire_subscriptions`, ...)
- [x] Регистрация парсеров в воркер-процессе (`register_default_parsers()` на
      импорте модуля вместо arq `on_startup`)
- [x] Таймауты: `run_parser` time_limit/soft_time_limit = 21600/21540 (как было
      `FULL_SYNC_LOCK_TTL`), `prune_history` 3600/3540

### Точки постановки в очередь
- [x] `backend/src/modules/parser/service/queue.py` — `enqueue_parser_run` через
      `celery_app.send_task("run_parser", ...)` (в `asyncio.to_thread`),
      возврат `task.id` вместо arq `job_id`
- [x] `backend/src/modules/mail/service/queue.py` — `_enqueue` через
      `send_task("send_password_mail", ...)`; arq-пул и `close_mail_queue` удалены
- [x] `backend/src/modules/mail/__init__.py` — экспорт `close_mail_queue` удалён
- [x] `backend/src/modules/broadcast/service/broadcast_service.py` —
      `_enqueue_broadcast` через `send_task("send_broadcast", ...)`; текст ошибки
      503 обновлён (без «arq src.worker…»)

### API / lifespan
- [x] `backend/src/main.py` — удалены `close_parser_queue` (импорт + вызов)

### Инфраструктура
- [x] `docker-compose.yml` — сервис `worker`: `celery -A src.worker worker
      --concurrency=1`, healthcheck `celery inspect ping`
- [x] `docker-compose.yml` — новый сервис `beat` (расписание пишется в `/tmp`,
      pidfile `/tmp/celerybeat.pid` — в `/app` права не позволяют);
      healthcheck по pidfile
- [x] `docker-compose.yml` — новый сервис `flower` (порт 5555): healthcheck на
      5555 через urllib; `FLOWER_UNAUTHENTICATED_API` по умолчанию true (dev),
      в проде выключить и включить `--basic_auth`
- [x] `docker compose up -d --build worker beat flower` — все три контейнера
      `healthy`

### Тесты
- [x] `backend/tests/integration/test_worker_jobs.py` — импорты и вызовы без
      `ctx`/`WorkerSettings`; расписание проверяется по `beat_schedule`
- [x] `backend/tests/integration/test_retention.py` — проверка регистрации
      `prune_history` через celery/beat, вызов `_prune_history(db=...)`

### Проверки
- [x] `ruff check src tests` — чисто
- [x] `ruff format --check src tests` — чисто
- [x] `python -m pytest tests/unit` — 385 passed
- [x] `python -m pytest tests/integration` — 675 passed
- [x] Smoke: локальный celery-воркер взял задачу (expire_subscriptions → succeeded);
      docker-воркер выполнил cleanup_refresh_tokens; Flower HTTP 200 + задача
      видна в `/api/tasks`
- [x] `docker compose config -q` — валиден; контейнеры worker/beat/flower подняты

## Прочее, что затронуто миграцией (не код)
- [x] `docs/plan/INDEX.md` — строка блока 08: «arq worker» → «celery worker»
- [x] Аудит: ссылок на `arq`/`WorkerSettings` в `src/` и `tests/` не осталось
- [x] Отчёт обновлён: галочки проставлены по факту выполнения

## Как запускать и мониторить

```bash
docker compose up -d --build worker beat flower

# Flower (очередь, in-progress, failed, ретраи): http://localhost:5555
# статусы парсеров по магазинам: /admin в приложении (poll 5с)
```

## Замечания

- `backend/poetry.lock` содержит устаревшие записи (arq). Файл не используется
  (воркфлоу — pip), poetry в окружении нет; обновить при возврате к poetry.
- `docs/audit/audit.md`, `docs/sprints/sprint-001-backend-api.md` — исторические
  документы планирования с упоминаниями arq; не переписывались.
- Крон-расписания переехали в `beat` 1:1 (03:00 каталог, 07:30/13:30/19:30 цены,
  :05 подписки, 04:30 токены, вс 04:45 чистка) — всё в UTC, как было в arq.
- Воркер с `--concurrency=1` (тяжёлые async-задачи). При росте нагрузки —
  выделить очередь `parser` с отдельным воркером.
- Полный синк каталога по-прежнему под флагом `PARSER_FULL_SYNC_ENABLED`
  (по умолчанию выключен).
- `job_id` в `ParserRunResponse` теперь = celery `task.id` (тот же uuid-формат,
  фронт не менялся).