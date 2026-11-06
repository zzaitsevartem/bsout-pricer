import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
backend = root / "backend"
kind = sys.argv[1]
targets = {
    "unit": ["tests/unit/test_search_predicate.py", "tests/unit/test_normalizer.py"],
    "integration": ["tests/integration/test_search_vocabulary.py"],
}[kind]
env = os.environ.copy()
env.update({
    "PYTHONPATH": str(backend),
    "TEST_DATABASE_URL": "postgresql+asyncpg://postgres:temporary-test-only@127.0.0.1:64889/postgres",
    "REDIS_HOST": "127.0.0.1",
    "REDIS_PORT": "64904",
    "JWT_SECRET_KEY": "test-only-secret-1234567890-abcdefghijklmnop",
    "DEBUG": "false",
})
command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rs", "--tb=short", "-x"]
command += [str(backend / target) for target in targets]
result = subprocess.run(command, cwd="/private/tmp", env=env, text=True, capture_output=True)
print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
if result.returncode or " skipped" in result.stdout or " skip" in result.stdout:
    raise SystemExit(result.returncode or 1)
print(f"{kind.upper()}_VOCABULARY_PASS")
