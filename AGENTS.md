# BScout Repository Rules

## Source of Truth

Run all commands from this Git repository, not the parent `bscount/` directory.
Trust code and current configuration over older prose. Read `DESIGN.md` before
UI work and `docs/technical-specification.md` before feature implementation.
Backend and frontend rules are refined by their nested `AGENTS.md` files.

`docs/plan/MASTERPLAN.md` is the only live task plan. At session start run:

```bash
bash scripts/plan/plan_status.sh
git log --oneline -10
git status --short
```

Do not create parallel TODO/plan documents. Closed details belong in
`docs/plan/archive/`; `docs/plan/INDEX.md` is the append-only block ledger.

## Architecture

- `backend/src/`: FastAPI, async SQLAlchemy, Redis, and module-based MVC.
- `backend/tests/{unit,integration}/`: Pytest suites.
- `frontend/src/`: Next.js App Router organized into `app/`, `models/`,
  `widgets/`, and `shared/`.
- `docs/`: specifications, audits, plans, and manual verification.
- `docker-compose.yml`, `infra/`, `deploy/`: local and production infrastructure.

## Commands

```bash
docker compose up -d
cd backend
source ../venv/bin/activate
pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m pytest tests/unit
ruff check src tests

cd ../frontend
npm install
npm run build
npm run lint
npm test
```

Use Python 3.11 and the existing `venv`/pip workflow; Poetry is not installed
for this checkout. Local ports may be overridden by gitignored environment
files; never read or edit real `.env` files. Use `.env.example` templates.

## Working Rules

- Preserve unrelated dirty-worktree changes.
- Do not commit unless explicitly asked.
- Do not create README or planning files without an explicit request.
- Add regression tests for fixes and verify changes proportionally to risk.
- Use the project skills under `.agents/skills/` for backend modules, frontend
  entities, UI/design work, and convention reviews.
