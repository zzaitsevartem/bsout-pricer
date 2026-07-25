#!/usr/bin/env bash
# Поднимает заархивированный блок обратно в MASTERPLAN (если работа переоткрылась):
# вставляет секцию между маркерами, флипает INDEX на [~]/MASTERPLAN, удаляет файл из archive/.
# Использование: bash scripts/plan/restore_block.sh NN
set -euo pipefail

NN="${1:?usage: restore_block.sh NN}"
SELF="${BASH_SOURCE[0]}"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"
PLAN="$ROOT/docs/plan/MASTERPLAN.md"
INDEX="$ROOT/docs/plan/INDEX.md"
ARCDIR="$ROOT/docs/plan/archive"

python3 - "$PLAN" "$INDEX" "$ARCDIR" "$NN" <<'PY'
import sys, re, os, glob
plan, index, arcdir, nn = sys.argv[1:5]

matches = sorted(glob.glob(os.path.join(arcdir, f"BLOCK-{nn}-*.md")) +
                 glob.glob(os.path.join(arcdir, f"BLOCK-{nn}.md")))
if not matches:
    sys.exit(f"Архивный файл блока {nn} не найден в {arcdir}.")
if len(matches) > 1:
    sys.exit(f"Найдено несколько файлов для блока {nn}: {matches}. Уточните вручную.")
arcfile = matches[0]

body = open(arcfile, encoding='utf-8').read()
body = re.sub(r"^<!-- Заархивировано.*?-->\n\n?", "", body, flags=re.S, count=1)
block = body.rstrip() + "\n\n"

s = open(plan, encoding='utf-8').read()
if re.search(rf"^## БЛОК {re.escape(nn)} ", s, flags=re.M):
    sys.exit(f"Блок {nn} уже присутствует в MASTERPLAN.")
s = re.sub(r"_Активных блоков нет.*?_\n\n", "", s, flags=re.S)
s = s.replace("<!-- BLOCKS:END -->", block + "<!-- BLOCKS:END -->", 1)
open(plan, 'w', encoding='utf-8').write(s)

title = re.match(r"## БЛОК \S+ — (.+)", block).group(1).strip()
lines = open(index, encoding='utf-8').read().splitlines()
for i, ln in enumerate(lines):
    if re.match(rf"\|\s*{re.escape(nn)}\s*\|", ln):
        lines[i] = f"| {nn} | {title} | [~] | — | MASTERPLAN |"
        break
open(index, 'w', encoding='utf-8').write("\n".join(lines) + "\n")

os.remove(arcfile)
print(f"Блок {nn} восстановлен в MASTERPLAN (INDEX → [~]), {os.path.basename(arcfile)} удалён из archive/.")
PY
