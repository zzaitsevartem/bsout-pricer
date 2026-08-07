# Backend Rules

## Architecture

Use Python 3.11, FastAPI, Pydantic v2, async SQLAlchemy, PostgreSQL, Redis, and
Alembic. Each feature under `src/modules/<name>/` follows:

- `model/`: SQLAlchemy models inheriting `Base`;
- `schema/`: request/response schemas;
- `service/`: business logic and database queries;
- `controller/`: FastAPI router exported as `<name>_router`.

Register routers in `src/main.py`. Register every new model in
`src/db_metadata.py`, which is imported by Alembic and tests.

## Conventions

- Keep endpoints, sessions, and database work async.
- Use `snake_case` in both Python and API JSON.
- Use `db: AsyncSession = Depends(get_db)`.
- Use `get_current_user` or `get_current_admin` from
  `src/modules/shared/deps.py` for authorization.
- Do not add docstrings or comments to production code.
- Never hardcode database credentials or read real `.env` files.
- Ruff enforces E/W/F/I, import order, formatting, and a 100-character line.

## Commands and Tests

Activate the repository venv and use pip, not Poetry:

```bash
source ../venv/bin/activate
pip install -r requirements-dev.txt
python -m alembic upgrade head
uvicorn src.main:app --reload --port 8010
python -m pytest tests/unit
python -m pytest
ruff format src tests
ruff check src tests
```

Unit tests must not require PostgreSQL, Redis, or the network. Mark service-backed
tests `integration`; the full suite requires Docker services and `bscout_test`.
Name tests `test_*.py` and add regression coverage for fixes. Create migrations
with `python -m alembic revision --autogenerate -m "description"` and inspect
generated operations before applying them.
