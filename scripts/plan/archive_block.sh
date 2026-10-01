#!/usr/bin/env bash
# Архивирует ЦЕЛИКОМ закрытый блок: вырезает секцию из MASTERPLAN → docs/plan/archive/,
# флипает строку в INDEX. Отказывается, если в блоке остались [ ] или [~].
# Использование: bash scripts/plan/archive_block.sh NN
set -euo pipefail

NN="${1:?usage: archive_block.sh NN}"
SELF="${BASH_SOURCE[0]}"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"
PLAN="$ROOT/docs/plan/MASTERPLAN.md"
INDEX="$ROOT/docs/plan/INDEX.md"
ARCDIR="$ROOT/docs/plan/archive"
DATE="$(date +%F)"
mkdir -p "$ARCDIR"

python3 - "$PLAN" "$INDEX" "$ARCDIR" "$NN" "$DATE" <<'PY'
import sys, re, os
plan, index, arcdir, nn, date = sys.argv[1:6]

s = open(plan, encoding='utf-8').read()
m = re.search(rf"(^## БЛОК {re.escape(nn)} .*?)(?=^## БЛОК |<!-- BLOCKS:END -->)",
              s, flags=re.S | re.M)
if not m:
    sys.exit(f"Блок {nn} не найден в активном MASTERPLAN (уже заархивирован?).")

block = m.group(1).rstrip() + "\n"
if re.search(r"^\s*- \[[ ~]\]", block, flags=re.M):
    sys.exit(f"Блок {nn} не закрыт целиком (есть [ ] или [~]). Архивация отменена.")

title = re.match(r"## БЛОК \S+ — (.+)", block).group(1).strip()
slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
fname = f"BLOCK-{nn}-{slug}.md" if slug else f"BLOCK-{nn}.md"
loc = f"archive/{fname}"

header = f"<!-- Заархивировано {date}. Восстановить: bash scripts/plan/restore_block.sh {nn} -->\n\n"
open(os.path.join(arcdir, fname), 'w', encoding='utf-8').write(header + block)

s = s[:m.start()] + s[m.end():]
if "## БЛОК " not in s.split("<!-- BLOCKS:START", 1)[-1].split("<!-- BLOCKS:END", 1)[0]:
    s = s.replace(
        "<!-- BLOCKS:END -->",
        "_Активных блоков нет. Заведите первый: `bash scripts/plan/new_block.sh 01 \"Название блока\"`._\n\n<!-- BLOCKS:END -->",
        1,
    )
open(plan, 'w', encoding='utf-8').write(s)

lines = open(index, encoding='utf-8').read().splitlines()
flipped = False
for i, ln in enumerate(lines):
    if re.match(rf"\|\s*{re.escape(nn)}\s*\|", ln):
        lines[i] = f"| {nn} | {title} | [x] | {date} | {loc} |"
        flipped = True
        break
if not flipped:
    lines.append(f"| {nn} | {title} | [x] | {date} | {loc} |")
open(index, 'w', encoding='utf-8').write("\n".join(lines) + "\n")

print(f"Блок {nn} → {loc}. INDEX обновлён (статус [x], дата {date}).")
PY

echo "Готово. Проверьте git diff; закоммитьте по просьбе: docs(plan): archive block ${NN}"
