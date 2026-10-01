#!/usr/bin/env bash
# SessionStart hook: подкладывает в контекст агента ТОЛЬКО сводку статуса плана
# (без чтения всего MASTERPLAN). Тихо выходит, если плана ещё нет.
set -euo pipefail

SELF="${BASH_SOURCE[0]}"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"
PLAN="$ROOT/docs/plan/MASTERPLAN.md"
[ -f "$PLAN" ] || exit 0

STATUS="$(bash "$ROOT/scripts/plan/plan_status.sh" 2>/dev/null || true)"
[ -z "$STATUS" ] && exit 0

CTX="[Планирование BScout] Единый источник задач — docs/plan/MASTERPLAN.md (полная карта: docs/plan/INDEX.md). Текущее состояние:

$STATUS

Протокол: найдите первый [ ], доложите активный блок и следующий шаг. НЕ перечитывайте план целиком — детали закрытых блоков лежат в docs/plan/archive/ и поднимаются по требованию."

python3 -c 'import sys,json; print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}}))' "$CTX"
exit 0
