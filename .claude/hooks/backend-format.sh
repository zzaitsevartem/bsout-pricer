#!/usr/bin/env bash
# PostToolUse (Edit|Write): ruff format + ruff check --fix для изменённого backend-файла.
# Тихо пропускается, если файл не в backend/ или ruff не установлен.
# ruff пока НЕ в зависимостях — добавьте: cd backend && poetry add --group dev ruff
set -euo pipefail

SELF="${BASH_SOURCE[0]}"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"

FILE="$(python3 -c 'import sys,json; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)"
[ -z "$FILE" ] && exit 0

case "$FILE" in
  *backend/*.py) ;;
  *) exit 0 ;;
esac

BE="$ROOT/backend"
REL="${FILE##*backend/}"
cd "$BE"

if command -v ruff >/dev/null 2>&1; then
  ruff format "$REL"      >/dev/null 2>&1 || true
  ruff check --fix "$REL" >/dev/null 2>&1 || true
elif poetry run ruff --version >/dev/null 2>&1; then
  poetry run ruff format "$REL"      >/dev/null 2>&1 || true
  poetry run ruff check --fix "$REL" >/dev/null 2>&1 || true
fi
exit 0
