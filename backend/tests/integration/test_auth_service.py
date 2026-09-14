import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.modules.auth.model.user import User
from src.modules.auth.service.auth import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_id,
    verify_password,
)

pytestmark = pytest.mark.integration

PASSWORD = "s3cret-pass"


async def _create(
    db,
    email: str = "user@example.com",
    password: str = PASSWORD,
    full_name: str = "Test User",
    phone: str | None = None,
    company: str | None = None,
) -> User:
    return await create_user(
        db,
        email=email,
        password=password,
        full_name=full_name,
        phone=phone,
        company=company,
    )


async def test_create_user_persists_row_with_all_fields(db_session):
    user = await _create(
        db_session,
        email="persist@example.com",
        full_name="Persist User",
        phone="+79001234567",
        company="BScout",
    )

    assert user.id is not None
    user_id = user.id

    db_session.expire_all()
    stored = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()

    assert stored.email == "persist@example.com"
    assert stored.full_name == "Persist User"
    assert stored.phone == "+79001234567"
    assert stored.company == "BScout"
    assert stored.is_active is True
    assert stored.is_admin is False
    assert stored.created_at is not None
    assert stored.updated_at is not None


async def test_create_user_allows_null_phone_and_company(db_session):
    user_id = (await _create(db_session, email="minimal@example.com")).id

    db_session.expire_all()
    stored = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()

    assert stored.phone is None
    assert stored.company is None


async def test_create_user_stores_bcrypt_hash_not_plaintext(db_session):
    user = await _create(db_session, email="hash@example.com")

    assert user.password_hash != PASSWORD
    assert PASSWORD not in user.password_hash
    assert user.password_hash.startswith("$2")
    assert len(user.password_hash) >= 59
    assert verify_password(PASSWORD, user.password_hash) is True
    assert verify_password("wrong-password", user.password_hash) is False


async def test_identical_passwords_get_distinct_salted_hashes(db_session):
    first = await _create(db_session, email="salt-a@example.com")
    second = await _create(db_session, email="salt-b@example.com")

    assert first.password_hash != second.password_hash
    assert verify_password(PASSWORD, first.password_hash) is True
    assert verify_password(PASSWORD, second.password_hash) is True


async def test_duplicate_email_violates_unique_constraint(db_session):
    await _create(db_session, email="dup@example.com", full_name="First")

    db_session.add(
        User(
            email="dup@example.com",
            password_hash="irrelevant",
            full_name="Second",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_create_user_with_duplicate_email_raises_integrity_error(db_session):
    await _create(db_session, email="dup-service@example.com", full_name="First")

    with pytest.raises(IntegrityError):
        await _create(
            db_session,
            email="dup-service@example.com",
            password="another-pass",
            full_name="Second",
        )


async def test_authenticate_user_returns_user_for_correct_credentials(db_session):
    created = await _create(db_session, email="auth-ok@example.com")

    authenticated = await authenticate_user(db_session, "auth-ok@example.com", PASSWORD)

    assert authenticated is not None
    assert authenticated.id == created.id
    assert authenticated.email == "auth-ok@example.com"


async def test_authenticate_user_returns_none_for_wrong_password(db_session):
    await _create(db_session, email="auth-bad-pass@example.com")

    assert await authenticate_user(db_session, "auth-bad-pass@example.com", "not-my-pass") is None


async def test_authenticate_user_returns_none_for_empty_password(db_session):
    await _create(db_session, email="auth-empty@example.com")

    assert await authenticate_user(db_session, "auth-empty@example.com", "") is None


async def test_authenticate_user_returns_none_for_unknown_email(db_session):
    await _create(db_session, email="known@example.com")

    assert await authenticate_user(db_session, "nobody@example.com", PASSWORD) is None


async def test_authenticate_user_does_not_accept_another_users_password(db_session):
    await _create(db_session, email="alice@example.com", password="alice-secret")
    await _create(db_session, email="bob@example.com", password="bob-secret")

    assert await authenticate_user(db_session, "alice@example.com", "bob-secret") is None


async def test_get_user_by_email_returns_matching_user(db_session):
    created = await _create(db_session, email="by-email@example.com", full_name="By Email")
    await _create(db_session, email="other@example.com", full_name="Other")

    found = await get_user_by_email(db_session, "by-email@example.com")

    assert found is not None
    assert found.id == created.id
    assert found.full_name == "By Email"


async def test_get_user_by_email_returns_none_when_missing(db_session):
    await _create(db_session, email="present@example.com")

    assert await get_user_by_email(db_session, "absent@example.com") is None


async def test_email_matching_is_case_insensitive(db_session):
    upper = await _create(db_session, email="Mixed@Example.com", full_name="Upper")

    found = await get_user_by_email(db_session, "mixed@example.com")
    assert found is not None
    assert found.id == upper.id

    assert await authenticate_user(db_session, "MIXED@example.com", PASSWORD) is not None


async def test_email_uniqueness_is_case_insensitive(db_session):
    await _create(db_session, email="Dup@Example.com", full_name="First")

    with pytest.raises(IntegrityError):
        await _create(db_session, email="dup@example.com", full_name="Second")


async def test_known_gap_bcrypt_ignores_password_bytes_beyond_72(db_session):
    long_password = "p" * 72
    await _create(db_session, email="long@example.com", password=long_password)

    assert await authenticate_user(db_session, "long@example.com", long_password + "x") is not None
    assert await authenticate_user(db_session, "long@example.com", "p" * 71) is None


async def test_get_user_by_id_returns_matching_user(db_session):
    created = await _create(db_session, email="by-id@example.com", full_name="By Id")
    await _create(db_session, email="by-id-other@example.com", full_name="Other")

    found = await get_user_by_id(db_session, created.id)

    assert found is not None
    assert found.email == "by-id@example.com"
    assert found.full_name == "By Id"


async def test_get_user_by_id_returns_none_when_missing(db_session):
    created = await _create(db_session, email="only@example.com")

    assert await get_user_by_id(db_session, created.id + 1000) is None
