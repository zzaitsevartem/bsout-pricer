import pytest

from src.modules.auth.service.auth import hash_password, verify_password

pytestmark = pytest.mark.unit


def test_hash_is_not_plaintext():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert hashed.startswith("$2")


def test_verify_accepts_correct_password():
    hashed = hash_password("s3cret-pass")
    assert verify_password("s3cret-pass", hashed) is True


def test_verify_rejects_wrong_password():
    hashed = hash_password("s3cret-pass")
    assert verify_password("wrong", hashed) is False


def test_same_password_hashes_differ_by_salt():
    assert hash_password("same") != hash_password("same")
