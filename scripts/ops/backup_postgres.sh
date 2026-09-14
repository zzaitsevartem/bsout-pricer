#!/usr/bin/env bash
# Снятие резервной копии БД BScout.
#
# Использование:
#   scripts/ops/backup_postgres.sh [каталог_бэкапов]
#
# Переменные окружения (значения по умолчанию — как в backend/.env.example):
#   POSTGRES_HOST (localhost), POSTGRES_PORT (5432), POSTGRES_DB (bscout),
#   POSTGRES_USER (bscout), POSTGRES_PASSWORD (обязательна, если нет ~/.pgpass),
#   BACKUP_DIR (./backups), BACKUP_KEEP (14) — сколько копий оставлять.
#
# Формат дампа — custom (-Fc), уже сжатый, восстанавливается через pg_restore.

set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-bscout}"
POSTGRES_USER="${POSTGRES_USER:-bscout}"
BACKUP_DIR="${1:-${BACKUP_DIR:-./backups}}"
BACKUP_KEEP="${BACKUP_KEEP:-14}"

if ! command -v pg_dump >/dev/null 2>&1; then
    echo "ОШИБКА: не найден pg_dump. Установите клиент PostgreSQL 16." >&2
    exit 1
fi

if [ -z "${POSTGRES_PASSWORD:-}" ] && [ ! -f "${HOME}/.pgpass" ]; then
    echo "ОШИБКА: не задан POSTGRES_PASSWORD и нет ~/.pgpass — подключиться нечем." >&2
    exit 1
fi

if [ -n "${POSTGRES_PASSWORD:-}" ]; then
    export PGPASSWORD="${POSTGRES_PASSWORD}"
fi

mkdir -p "${BACKUP_DIR}"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="${BACKUP_DIR}/bscout-${POSTGRES_DB}-${TIMESTAMP}.dump"
TMP_TARGET="${TARGET}.part"

# Незавершённый дамп не должен остаться и быть принят за годную копию.
cleanup_partial() {
    if [ -f "${TMP_TARGET}" ]; then
        rm -f "${TMP_TARGET}"
        echo "Частичный файл ${TMP_TARGET} удалён." >&2
    fi
}
trap cleanup_partial EXIT

echo "Снимаю бэкап ${POSTGRES_DB} с ${POSTGRES_HOST}:${POSTGRES_PORT} в ${TARGET} ..."

if ! pg_dump \
    --host="${POSTGRES_HOST}" \
    --port="${POSTGRES_PORT}" \
    --username="${POSTGRES_USER}" \
    --dbname="${POSTGRES_DB}" \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    --file="${TMP_TARGET}"; then
    echo "ОШИБКА: pg_dump завершился с ненулевым кодом, бэкап НЕ создан." >&2
    exit 1
fi

if [ ! -s "${TMP_TARGET}" ]; then
    echo "ОШИБКА: дамп получился пустым — считаем бэкап неудачным." >&2
    exit 1
fi

# Проверяем, что дамп читается pg_restore, иначе копия бесполезна.
if ! pg_restore --list "${TMP_TARGET}" >/dev/null 2>&1; then
    echo "ОШИБКА: pg_restore не смог прочитать оглавление дампа — файл повреждён." >&2
    exit 1
fi

mv "${TMP_TARGET}" "${TARGET}"
trap - EXIT

SIZE="$(du -h "${TARGET}" | cut -f1)"
echo "Готово: ${TARGET} (${SIZE})"

# Ротация: оставляем BACKUP_KEEP самых свежих дампов этой БД, остальные удаляем.
# Без mapfile — скрипт должен работать и на bash 3.2 (macOS).
ROTATED=0
while IFS= read -r old; do
    [ -n "${old}" ] || continue
    rm -f "${old}"
    echo "Ротация: удалён старый бэкап ${old}"
    ROTATED=$((ROTATED + 1))
done <<EOF
$(ls -1t "${BACKUP_DIR}"/bscout-"${POSTGRES_DB}"-*.dump 2>/dev/null | tail -n +"$((BACKUP_KEEP + 1))")
EOF

if [ "${ROTATED}" -eq 0 ]; then
    echo "Ротация: удалять нечего (храним последние ${BACKUP_KEEP})."
fi
