#!/usr/bin/env bash
# Восстановление БД BScout из дампа, снятого backup_postgres.sh.
#
# ВНИМАНИЕ: операция РАЗРУШАЮЩАЯ — существующие данные целевой базы будут затёрты.
# Скрипт НИКОГДА не выполняется молча: он требует ввести имя целевой БД вручную
# либо явный флаг --yes-i-know-what-i-am-doing (для отрепетированных runbook-сценариев).
#
# Использование:
#   scripts/ops/restore_postgres.sh backups/bscout-bscout-20260727T031500Z.dump
#   scripts/ops/restore_postgres.sh <файл> --yes-i-know-what-i-am-doing
#
# Переменные окружения:
#   POSTGRES_HOST (localhost), POSTGRES_PORT (5432), POSTGRES_DB (bscout),
#   POSTGRES_USER (bscout), POSTGRES_PASSWORD (или ~/.pgpass),
#   RESTORE_JOBS (4) — параллелизм pg_restore.

set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-bscout}"
POSTGRES_USER="${POSTGRES_USER:-bscout}"
RESTORE_JOBS="${RESTORE_JOBS:-4}"

DUMP_FILE="${1:-}"
CONFIRM_FLAG="${2:-}"

if [ -z "${DUMP_FILE}" ]; then
    echo "Использование: $0 <файл-дампа> [--yes-i-know-what-i-am-doing]" >&2
    exit 1
fi

if [ ! -f "${DUMP_FILE}" ]; then
    echo "ОШИБКА: файл дампа не найден: ${DUMP_FILE}" >&2
    exit 1
fi

for tool in pg_restore psql; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "ОШИБКА: не найден ${tool}. Установите клиент PostgreSQL 16." >&2
        exit 1
    fi
done

if [ -z "${POSTGRES_PASSWORD:-}" ] && [ ! -f "${HOME}/.pgpass" ]; then
    echo "ОШИБКА: не задан POSTGRES_PASSWORD и нет ~/.pgpass — подключиться нечем." >&2
    exit 1
fi

if [ -n "${POSTGRES_PASSWORD:-}" ]; then
    export PGPASSWORD="${POSTGRES_PASSWORD}"
fi

# Битый дамп лучше обнаружить ДО того, как база затёрта.
if ! pg_restore --list "${DUMP_FILE}" >/dev/null 2>&1; then
    echo "ОШИБКА: ${DUMP_FILE} не читается pg_restore — восстановление отменено." >&2
    exit 1
fi

echo "==================================================================="
echo " ВНИМАНИЕ: РАЗРУШАЮЩАЯ ОПЕРАЦИЯ"
echo "-------------------------------------------------------------------"
echo " Дамп:    ${DUMP_FILE}"
echo " Сервер:  ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo " База:    ${POSTGRES_DB}"
echo ""
echo " Все текущие данные базы ${POSTGRES_DB} будут УДАЛЕНЫ и заменены"
echo " содержимым дампа. Пользователи, платежи и история цен —"
echo " на состояние на момент снятия копии."
echo "==================================================================="

if [ "${CONFIRM_FLAG}" = "--yes-i-know-what-i-am-doing" ]; then
    echo "Подтверждение получено флагом --yes-i-know-what-i-am-doing."
else
    if [ ! -t 0 ]; then
        echo "ОШИБКА: неинтерактивный запуск без --yes-i-know-what-i-am-doing." >&2
        echo "Молча затирать базу скрипт отказывается." >&2
        exit 1
    fi
    printf 'Для продолжения введите имя базы (%s): ' "${POSTGRES_DB}"
    read -r ANSWER
    if [ "${ANSWER}" != "${POSTGRES_DB}" ]; then
        echo "Введено '${ANSWER}' вместо '${POSTGRES_DB}'. Восстановление ОТМЕНЕНО." >&2
        exit 1
    fi
fi

echo "Отключаю остальные сессии к ${POSTGRES_DB} ..."
psql \
    --host="${POSTGRES_HOST}" \
    --port="${POSTGRES_PORT}" \
    --username="${POSTGRES_USER}" \
    --dbname=postgres \
    --quiet \
    --no-psqlrc \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
        WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid()" >/dev/null

echo "Восстанавливаю ${POSTGRES_DB} из ${DUMP_FILE} ..."

# --clean --if-exists сносит объекты перед накатом; расширения (pg_trgm, citext)
# и GIN-индексы приезжают из самого дампа, отдельного alembic upgrade не требуется.
if ! pg_restore \
    --host="${POSTGRES_HOST}" \
    --port="${POSTGRES_PORT}" \
    --username="${POSTGRES_USER}" \
    --dbname="${POSTGRES_DB}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    --jobs="${RESTORE_JOBS}" \
    --exit-on-error \
    "${DUMP_FILE}"; then
    echo "ОШИБКА: pg_restore завершился с ненулевым кодом. База может быть в" >&2
    echo "частично восстановленном состоянии — НЕ пускайте трафик, разбирайтесь." >&2
    exit 1
fi

echo "Проверяю версию схемы (alembic_version) ..."
psql \
    --host="${POSTGRES_HOST}" \
    --port="${POSTGRES_PORT}" \
    --username="${POSTGRES_USER}" \
    --dbname="${POSTGRES_DB}" \
    --no-psqlrc \
    -c "SELECT version_num AS alembic_version FROM alembic_version"

echo "Готово. База ${POSTGRES_DB} восстановлена из ${DUMP_FILE}."
echo "Дальше: сверьте alembic_version с текущим кодом и при необходимости"
echo "выполните 'python -m alembic upgrade head'."
