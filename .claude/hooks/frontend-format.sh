#!/usr/bin/env bash
# PostToolUse (Edit|Write): prettier --write + eslint --fix для изменённого фронтенд-файла.
# Тихо пропускается, если файл не в frontend/ или зависимости ещё не установлены.
set -euo pipefail

SELF="${BASH_SOURCE[0]}"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"   # .claude/hooks/ -> корень проекта

FILE="$(python3 -c 'import sys,json; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)"
[ -z "$FILE" ] && exit 0

case "$FILE" in
  *frontend/*.ts|*frontend/*.tsx) ;;
  *) exit 0 ;;
esac

FE="$ROOT/frontend"
[ -d "$FE/node_modules" ] || exit 0   # npm install ещё не делали — пропускаем

REL="${FILE##*frontend/}"
cd "$FE"
npx --no-install prettier --write "$REL" >/dev/null 2>&1 || true
npx --no-install eslint --fix "$REL"   >/dev/null 2>&1 || true
exit 0
