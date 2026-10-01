#!/usr/bin/env bash
# PreToolUse guard: блокирует доступ к реальным секрет-файлам (.env и производные).
# .env.example и любые *.example/*.sample/*.template — разрешены (это шаблоны).
# Срабатывает на Read|Edit|Write (по file_path) и Bash (по токенам команды).
# Решение возвращается как permissionDecision:"deny" (JSON на stdout, exit 0).
#
# ВАЖНО: JSON хука приходит на stdin, поэтому сначала читаем его в переменную,
# а python-код передаём через heredoc (иначе heredoc занял бы stdin).
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 - <<'PY'
import os, json, shlex, sys

try:
    data = json.loads(os.environ.get("HOOK_INPUT", "") or "{}")
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
ti = data.get("tool_input", {}) or {}

def is_secret(p):
    p = str(p).strip().strip('"').strip("'").lstrip("<>|&")
    base = p.rsplit("/", 1)[-1]
    if base.endswith((".example", ".sample", ".template")):
        return False
    return base == ".env" or base.startswith(".env.")

hit = None

for k in ("file_path", "path", "notebook_path"):
    v = ti.get(k)
    if v and is_secret(v):
        hit = str(v)
        break

if not hit and tool == "Bash":
    cmd = ti.get("command", "") or ""
    try:
        toks = shlex.split(cmd)
    except Exception:
        toks = cmd.split()
    for t in toks:
        if is_secret(t):
            hit = t
            break

if hit:
    reason = (
        "Заблокировано protect-secrets: доступ к секрет-файлу '%s'. "
        "Реальные .env не должны читаться агентом или попадать в git — "
        "используйте .env.example как шаблон." % hit
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }))

sys.exit(0)
PY
