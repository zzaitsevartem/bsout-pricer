import sys
sys.path.insert(0, '/tmp/hot30-test-deps')
import pytest
code = pytest.main(['/tmp/hot30-tests/unit/test_extractor.py', '-q', '-o', 'addopts='])
if code:
    raise SystemExit(code)
print('HOT30_REGRESSIONS_VERIFIED')
