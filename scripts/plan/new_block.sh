#!/usr/bin/env bash
# Заводит новый блок: скелет в MASTERPLAN (между маркерами BLOCKS) + строка в INDEX.
# Использование: bash scripts/plan/new_block.sh NN "Название блока"
set -euo pipefail

NN="${1:?usage: new_block.sh NN \"Title\"}"
TITLE="${2:?usage: new_block.sh NN \"Title\"}"
SELF="${BASH_SOURCE[0]}"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"
PLAN="$ROOT/docs/plan/MASTERPLAN.md"
INDEX="$ROOT/docs/plan/INDEX.md"
DATE="$(date +%F)"

[ -f "$PLAN" ] || { echo "MASTERPLAN.md не найден ($PLAN)"; exit 1; }

python3 - "$PLAN" "$INDEX" "$NN" "$TITLE" "$DATE" <<'PY'
import sys, re
plan, index, nn, title, date = sys.argv[1:6]

s = open(plan, encoding='utf-8').read()
if re.search(rf"^## БЛОК {re.escape(nn)} ", s, flags=re.M):
    sys.exit(f"Блок {nn} уже есть в MASTERPLAN — выберите другой номер.")

if "<!-- BLOCKS:END -->" not in s:
    sys.exit("Маркер <!-- BLOCKS:END --> не найден в MASTERPLAN — не могу вставить блок.")

block = (
    f"## БЛОК {nn} — {title}\n\n"
    f"**Статус:** [ ] · **Заведён:** {date}\n\n"
    f"- [ ] (опишите первый пункт)\n\n"
)

s = re.sub(r"_Активных блоков нет.*?_\n\n", "", s, flags=re.S)
s = s.replace("<!-- BLOCKS:END -->", block + "<!-- BLOCKS:END -->", 1)
open(plan, 'w', encoding='utf-8').write(s)

with open(index, 'a', encoding='utf-8') as f:
    f.write(f"| {nn} | {title} | [ ] | — | MASTERPLAN |\n")

print(f"Блок {nn} добавлен в MASTERPLAN и INDEX.")
print("Не забудьте обновить «Текущий статус» в MASTERPLAN.md.")
PY
