import pytest
from sqlalchemy import func, select

from src.cli import (
    ADMIN_MESSAGES,
    ADMIN_PASSWORD_ENV,
    AdminBootstrapError,
    create_admin,
    read_admin_password,
)
from src.modules.auth.model.user import User
from src.modules.auth.service.auth import authenticate_user, create_user, verify_password
from src.modules.auth.service.security import WeakCredentialsError

pytestmark = pytest.mark.integration

EMAIL = "root@example.com"
PASSWORD = "s3cret-pass"


class PasswordProvider:
    def __init__(self, password: str = PASSWORD):
        self.password = password
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        return self.password


async def _bootstrap(db, email: str = EMAIL, full_name: str = "Root", promote: bool = False):
    provider = PasswordProvider()
    outcome = await create_admin(db, email, full_name, promote, provider)
    return outcome, provider


async def _count_users(db) -> int:
    return (await db.execute(select(func.count()).select_from(User))).scalar_one()


async def _load(db, email: str = EMAIL) -> User:
    return (await db.execute(select(User).where(User.email == email))).scalar_one()


async def test_create_admin_creates_an_active_administrator(db_session):
    outcome, _ = await _bootstrap(db_session)

    user = await _load(db_session)

    assert outcome == "created"
    assert user.is_admin is True
    assert user.is_active is True
    assert user.full_name == "Root"


async def test_create_admin_stores_a_hashed_password(db_session):
    await _bootstrap(db_session)

    user = await _load(db_session)

    assert user.password_hash != PASSWORD
    assert verify_password(PASSWORD, user.password_hash) is True


async def test_the_bootstrapped_admin_can_authenticate(db_session):
    await _bootstrap(db_session)

    authenticated = await authenticate_user(db_session, EMAIL, PASSWORD)

    assert authenticated is not None
    assert authenticated.is_admin is True


async def test_running_create_admin_twice_does_not_duplicate_the_user(db_session):
    await _bootstrap(db_session)

    outcome, provider = await _bootstrap(db_session)

    assert outcome == "exists_admin"
    assert await _count_users(db_session) == 1
    assert provider.calls == 0


async def test_repeat_run_reports_a_readable_message_instead_of_crashing(db_session):
    await _bootstrap(db_session)
    outcome, _ = await _bootstrap(db_session)

    assert "already an administrator" in ADMIN_MESSAGES[outcome].format(email=EMAIL)


async def test_existing_email_is_matched_case_insensitively(db_session):
    await _bootstrap(db_session, email="Root@Example.com")

    outcome, _ = await _bootstrap(db_session, email="root@example.com")

    assert outcome == "exists_admin"
    assert await _count_users(db_session) == 1


async def test_existing_plain_user_is_not_promoted_without_the_flag(db_session):
    await create_user(
        db_session, email=EMAIL, password=PASSWORD, full_name="Plain", phone=None, company=None
    )

    outcome, provider = await _bootstrap(db_session)

    assert outcome == "exists"
    assert (await _load(db_session)).is_admin is False
    assert provider.calls == 0


async def test_existing_plain_user_is_promoted_with_the_flag(db_session):
    await create_user(
        db_session, email=EMAIL, password=PASSWORD, full_name="Plain", phone=None, company=None
    )

    outcome, provider = await _bootstrap(db_session, promote=True)
    user = await _load(db_session)

    assert outcome == "promoted"
    assert user.is_admin is True
    assert user.full_name == "Plain"
    assert provider.calls == 0
    assert await _count_users(db_session) == 1


async def test_promotion_keeps_the_original_password(db_session):
    await create_user(
        db_session, email=EMAIL, password=PASSWORD, full_name="Plain", phone=None, company=None
    )

    await _bootstrap(db_session, promote=True)

    assert verify_password(PASSWORD, (await _load(db_session)).password_hash) is True


async def test_promoting_an_existing_admin_is_a_no_op(db_session):
    await _bootstrap(db_session)

    outcome, _ = await _bootstrap(db_session, promote=True)

    assert outcome == "exists_admin"
    assert await _count_users(db_session) == 1


async def test_weak_password_is_rejected_and_creates_nothing(db_session):
    with pytest.raises(WeakCredentialsError):
        await create_admin(db_session, EMAIL, "Root", False, PasswordProvider("123"))

    assert await _count_users(db_session) == 0


async def test_invalid_email_is_rejected_and_creates_nothing(db_session):
    with pytest.raises(WeakCredentialsError):
        await create_admin(db_session, "not-an-email", "Root", False, PasswordProvider())

    assert await _count_users(db_session) == 0


async def test_password_is_never_taken_from_the_command_line():
    from src.cli import _build_parser

    args = _build_parser().parse_args(["create-admin", "--email", EMAIL])

    assert not hasattr(args, "password")
    assert vars(args) == {
        "command": "create-admin",
        "email": EMAIL,
        "full_name": "Administrator",
        "promote": False,
    }


def test_password_is_read_from_the_environment_when_present(monkeypatch):
    monkeypatch.setenv(ADMIN_PASSWORD_ENV, PASSWORD)

    assert read_admin_password() == PASSWORD


def test_missing_password_without_a_tty_fails_loudly(monkeypatch):
    monkeypatch.delenv(ADMIN_PASSWORD_ENV, raising=False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    with pytest.raises(AdminBootstrapError) as exc_info:
        read_admin_password()

    assert ADMIN_PASSWORD_ENV in str(exc_info.value)


def test_mismatched_interactive_passwords_are_rejected(monkeypatch):
    monkeypatch.delenv(ADMIN_PASSWORD_ENV, raising=False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    answers = iter([PASSWORD, "something-else"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(answers))

    with pytest.raises(AdminBootstrapError) as exc_info:
        read_admin_password()

    assert "do not match" in str(exc_info.value)


def test_matching_interactive_passwords_are_accepted(monkeypatch):
    monkeypatch.delenv(ADMIN_PASSWORD_ENV, raising=False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", lambda prompt="": PASSWORD)

    assert read_admin_password() == PASSWORD
