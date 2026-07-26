import asyncio
import logging
import smtplib
import threading
import time

import pytest

from src.config import settings
from src.modules.mail import (
    MAIL_QUEUE_ENV_FLAG,
    ConsoleMailer,
    Mailer,
    MailError,
    MailMessage,
    MailNotConfiguredError,
    SmtpMailer,
    dispatch_mail,
    drain_pending_mail,
    get_mailer,
    password_reset_link,
    password_reset_message,
    queue_enabled,
)

pytestmark = pytest.mark.unit

TOKEN = "s3cr3t-reset-token-value"


class _RecordingSmtp:
    instances: list["_RecordingSmtp"] = []

    def __init__(self, host, port, timeout=None, context=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.logged_in: tuple[str, str] | None = None
        self.sent: list[tuple[str, list[str], str]] = []
        self.thread_ident = threading.get_ident()
        self.quit_called = False
        _RecordingSmtp.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.quit_called = True
        return False

    def login(self, user, password):
        self.logged_in = (user, password)

    def sendmail(self, sender, recipients, message):
        self.sent.append((sender, recipients, message))


@pytest.fixture(autouse=True)
def _reset_recorder():
    _RecordingSmtp.instances = []
    yield
    _RecordingSmtp.instances = []


def test_mailer_is_abstract():
    with pytest.raises(TypeError):
        Mailer()


def test_get_mailer_uses_console_backend_by_default(monkeypatch):
    monkeypatch.setattr(settings, "mail_backend", "console")

    mailer = get_mailer()

    assert isinstance(mailer, ConsoleMailer)
    assert mailer.backend == "console"


def test_get_mailer_returns_smtp_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "mail_backend", "smtp")

    mailer = get_mailer()

    assert isinstance(mailer, SmtpMailer)
    assert mailer.backend == "smtp"


def test_get_mailer_rejects_unknown_backend():
    with pytest.raises(MailError) as exc_info:
        get_mailer("carrier_pigeon")

    message = str(exc_info.value)
    assert "carrier_pigeon" in message
    assert "console" in message


async def test_console_mailer_never_raises(caplog):
    mailer = ConsoleMailer()

    with caplog.at_level(logging.INFO, logger="bscout.mail"):
        await mailer.send(
            to="user@example.com",
            subject="Восстановление пароля",
            text=f"Ссылка: https://bscout.ru/reset-password?token={TOKEN}",
        )

    assert any("user@example.com" in record.getMessage() for record in caplog.records)


async def test_console_mailer_does_not_log_token_or_link(caplog):
    mailer = ConsoleMailer()
    message = password_reset_message(TOKEN)

    with caplog.at_level(logging.DEBUG, logger="bscout.mail"):
        await mailer.send(
            to="victim@example.com",
            subject=message.subject,
            text=message.text,
            html=message.html,
        )

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "victim@example.com" in logged
    assert TOKEN not in logged
    assert "reset-password" not in logged


async def test_smtp_mailer_without_host_raises_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "mail_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "smtp_user", "bot@bscout.ru")
    monkeypatch.setattr(settings, "smtp_password", "secret")

    mailer = get_mailer()

    with pytest.raises(MailNotConfiguredError) as exc_info:
        await mailer.send(to="user@example.com", subject="s", text="t")

    message = str(exc_info.value)
    assert "smtp_host" in message


async def test_smtp_mailer_without_credentials_raises_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "mail_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.yandex.ru")
    monkeypatch.setattr(settings, "smtp_user", None)
    monkeypatch.setattr(settings, "smtp_password", None)

    mailer = get_mailer()

    with pytest.raises(MailNotConfiguredError) as exc_info:
        await mailer.send(to="user@example.com", subject="s", text="t")

    assert "smtp_user" in str(exc_info.value)


async def test_smtp_mailer_sends_over_ssl_in_a_worker_thread(monkeypatch):
    monkeypatch.setattr(settings, "mail_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.yandex.ru")
    monkeypatch.setattr(settings, "smtp_port", 465)
    monkeypatch.setattr(settings, "smtp_use_ssl", True)
    monkeypatch.setattr(settings, "smtp_user", "bot@bscout.ru")
    monkeypatch.setattr(settings, "smtp_password", "secret")
    monkeypatch.setattr(settings, "smtp_from", "BScout <no-reply@bscout.ru>")
    monkeypatch.setattr(smtplib, "SMTP_SSL", _RecordingSmtp)

    mailer = get_mailer()
    await mailer.send(
        to="user@example.com",
        subject="Восстановление пароля",
        text="текст письма",
        html="<p>текст письма</p>",
    )

    assert len(_RecordingSmtp.instances) == 1
    sent_smtp = _RecordingSmtp.instances[0]
    assert (sent_smtp.host, sent_smtp.port) == ("smtp.yandex.ru", 465)
    assert sent_smtp.logged_in == ("bot@bscout.ru", "secret")
    assert len(sent_smtp.sent) == 1
    _, recipients, raw = sent_smtp.sent[0]
    assert recipients == ["user@example.com"]
    assert "user@example.com" in raw
    assert sent_smtp.thread_ident != threading.get_ident()


async def test_smtp_failure_propagates_and_is_not_swallowed(monkeypatch):
    class _Failing(_RecordingSmtp):
        def sendmail(self, sender, recipients, message):
            raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

    monkeypatch.setattr(settings, "mail_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.yandex.ru")
    monkeypatch.setattr(settings, "smtp_user", "bot@bscout.ru")
    monkeypatch.setattr(settings, "smtp_password", "secret")
    monkeypatch.setattr(settings, "smtp_use_ssl", True)
    monkeypatch.setattr(smtplib, "SMTP_SSL", _Failing)

    mailer = get_mailer()

    with pytest.raises(MailError):
        await mailer.send(to="user@example.com", subject="s", text="t")


def test_password_reset_link_is_built_from_frontend_base_url(monkeypatch):
    monkeypatch.setattr(settings, "frontend_base_url", "https://bscout.ru")

    link = password_reset_link(TOKEN)

    assert link.startswith("https://bscout.ru/")
    assert TOKEN in link


def test_password_reset_link_ignores_trailing_slash_in_base_url(monkeypatch):
    monkeypatch.setattr(settings, "frontend_base_url", "https://bscout.ru/")

    link = password_reset_link(TOKEN)

    assert "//reset" not in link.replace("https://", "")
    assert link.startswith("https://bscout.ru/")


def test_password_reset_link_never_uses_request_host(monkeypatch):
    monkeypatch.setattr(settings, "frontend_base_url", "https://bscout.ru")

    link = password_reset_link(TOKEN)

    assert "evil.example.com" not in link
    assert link.startswith("https://bscout.ru/")


def test_password_reset_link_url_encodes_the_token(monkeypatch):
    monkeypatch.setattr(settings, "frontend_base_url", "https://bscout.ru")

    link = password_reset_link("a+b/c=d")

    assert "a+b/c=d" not in link
    assert "a%2Bb%2Fc%3Dd" in link


def test_password_reset_message_carries_link_in_text_and_html(monkeypatch):
    monkeypatch.setattr(settings, "frontend_base_url", "https://bscout.ru")

    message = password_reset_message(TOKEN)
    link = password_reset_link(TOKEN)

    assert isinstance(message, MailMessage)
    assert message.subject
    assert link in message.text
    assert link in message.html


async def test_console_mailer_send_is_awaitable_and_returns_none():
    result = await ConsoleMailer().send(to="a@b.ru", subject="s", text="t")

    assert result is None
    assert asyncio.iscoroutinefunction(ConsoleMailer.send)


def test_mail_queue_is_disabled_unless_explicitly_turned_on(monkeypatch):
    monkeypatch.delenv(MAIL_QUEUE_ENV_FLAG, raising=False)
    monkeypatch.delattr(settings, "mail_queue_enabled", raising=False)

    assert queue_enabled() is False


def test_mail_queue_reads_the_environment_flag(monkeypatch):
    monkeypatch.delattr(settings, "mail_queue_enabled", raising=False)
    monkeypatch.setenv(MAIL_QUEUE_ENV_FLAG, "true")

    assert queue_enabled() is True


async def test_dispatch_mail_returns_before_a_slow_delivery_finishes(monkeypatch):
    monkeypatch.delenv(MAIL_QUEUE_ENV_FLAG, raising=False)
    monkeypatch.delattr(settings, "mail_queue_enabled", raising=False)
    finished = []

    async def _slow(to, subject, text, html):
        await asyncio.sleep(0.2)
        finished.append(to)

    started = time.perf_counter()
    await dispatch_mail(_slow, "user@example.com", "s", "t", None)
    elapsed = time.perf_counter() - started

    assert elapsed < 0.1
    assert finished == []

    await drain_pending_mail()
    assert finished == ["user@example.com"]


async def test_dispatch_mail_completes_an_instant_delivery_before_returning(monkeypatch):
    monkeypatch.delenv(MAIL_QUEUE_ENV_FLAG, raising=False)
    monkeypatch.delattr(settings, "mail_queue_enabled", raising=False)
    delivered = []

    async def _instant(to, subject, text, html):
        delivered.append((to, subject))

    await dispatch_mail(_instant, "user@example.com", "subj", "body", None)

    assert delivered == [("user@example.com", "subj")]
