#!/usr/bin/env bash
# Печатает ТОЛЬКО сводку статуса + первый открытый пункт [ ] — для холодного старта
# без чтения всего MASTERPLAN. Используется и SessionStart-хуком.
set -euo pipefail

SELF="${BASH_SOURCE[0]}"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"
PLAN="$ROOT/docs/plan/MASTERPLAN.md"
[ -f "$PLAN" ] || { echo "MASTERPLAN.md не найден ($PLAN)"; exit 0; }

awk '
  /^## Текущий статус/ {f=1}
  f && /^## Легенда/    {exit}
  f {print}
' "$PLAN"

awk '
  /^## БЛОК /                 {block=$0}
  /^[[:space:]]*- \[ \]/ {
    if (!done) {
      print "";
      if (block != "") print "Следующий шаг — " block;
      sub(/^[[:space:]]*/, "");
      print "  " $0;
      done=1
    }
  }
  END { if (!done) print "\nОткрытых пунктов [ ] нет — заведите блок: bash scripts/plan/new_block.sh NN \"…\"" }
' "$PLAN"
