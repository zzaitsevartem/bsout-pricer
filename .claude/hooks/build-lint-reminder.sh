#!/usr/bin/env bash
# Stop hook: напоминает про конвенцию "npm run build && npm run lint",
# только если под frontend/src или backend/src есть незакоммиченные изменения.
# Не блокирует (continue не трогаем) — просто systemMessage.
set -euo pipefail

SELF="${BASH_SOURCE[0]}"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"
cd "$ROOT" 2>/dev/null || exit 0

command -v git >/dev/null 2>&1 || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

FE_CHANGED="$(git status --porcelain -- frontend/src 2>/dev/null || true)"
BE_CHANGED="$(git status --porcelain -- backend/src 2>/dev/null || true)"
[ -z "$FE_CHANGED" ] && [ -z "$BE_CHANGED" ] && exit 0

MSG="Напоминание (конвенция проекта): есть незакоммиченные изменения."
[ -n "$FE_CHANGED" ] && MSG="$MSG Фронтенд — прогони: cd frontend && npm run build && npm run lint."
[ -n "$BE_CHANGED" ] && MSG="$MSG Бэкенд — прогони: cd backend && source ../venv/bin/activate && python -m pytest tests/unit && ruff check src tests."

python3 -c 'import sys,json; print(json.dumps({"systemMessage": sys.argv[1]}))' "$MSG"
exit 0
