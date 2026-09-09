import asyncio
import logging
import smtplib
import ssl
from abc import ABC, abstractmethod
from collections.abc import Callable
from email.message import EmailMessage

from src.config import settings

CONSOLE_BACKEND = "console"
SMTP_BACKEND = "smtp"
MAIL_BACKENDS = (CONSOLE_BACKEND, SMTP_BACKEND)

SMTP_TIMEOUT = 30

logger = logging.getLogger("bscout.mail")


class MailError(RuntimeError):
    pass


class MailNotConfiguredError(MailError):
    pass


class Mailer(ABC):
    backend: str = CONSOLE_BACKEND

    @abstractmethod
    async def send(self, to: str, subject: str, text: str, html: str | None = None) -> None: ...


class ConsoleMailer(Mailer):
    backend = CONSOLE_BACKEND

    async def send(self, to: str, subject: str, text: str, html: str | None = None) -> None:
        logger.info("mail sent backend=%s to=%s subject=%s", self.backend, to, subject)
        return None


class SmtpMailer(Mailer):
    backend = SMTP_BACKEND

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        use_ssl: bool | None = None,
        sender: str | None = None,
        timeout: int = SMTP_TIMEOUT,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._use_ssl = use_ssl
        self._sender = sender
        self._timeout = timeout

    def _resolved(self) -> dict:
        host = self._host if self._host is not None else settings.smtp_host
        port = self._port if self._port is not None else settings.smtp_port
        user = self._user if self._user is not None else settings.smtp_user
        password = self._password if self._password is not None else settings.smtp_password
        use_ssl = self._use_ssl if self._use_ssl is not None else settings.smtp_use_ssl
        sender = self._sender if self._sender is not None else settings.smtp_from

        missing = [
            name
            for name, value in (
                ("smtp_host", host),
                ("smtp_user", user),
                ("smtp_password", password),
            )
            if not value
        ]
        if missing:
            raise MailNotConfiguredError(
                f"Почтовый бэкенд «{SMTP_BACKEND}» выбран, но не настроен: "
                f"не заданы {', '.join(missing)}. "
                f"Укажите их в .env или переключите mail_backend на «{CONSOLE_BACKEND}»."
            )

        return {
            "host": host,
            "port": int(port),
            "user": user,
            "password": password,
            "use_ssl": bool(use_ssl),
            "sender": sender,
        }

    def _build(self, config: dict, to: str, subject: str, text: str, html: str | None):
        message = EmailMessage()
        message["From"] = config["sender"]
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text)
        if html:
            message.add_alternative(html, subtype="html")
        return message

    def _send_sync(self, config: dict, to: str, message: EmailMessage) -> None:
        if config["use_ssl"]:
            client = smtplib.SMTP_SSL(
                config["host"],
                config["port"],
                timeout=self._timeout,
                context=ssl.create_default_context(),
            )
        else:
            client = smtplib.SMTP(config["host"], config["port"], timeout=self._timeout)
        with client as connection:
            if not config["use_ssl"]:
                connection.starttls(context=ssl.create_default_context())
            connection.login(config["user"], config["password"])
            connection.sendmail(config["sender"], [to], message.as_string())

    async def send(self, to: str, subject: str, text: str, html: str | None = None) -> None:
        config = self._resolved()
        message = self._build(config, to, subject, text, html)
        try:
            await asyncio.to_thread(self._send_sync, config, to, message)
        except MailError:
            raise
        except (smtplib.SMTPException, OSError) as exc:
            raise MailError(
                f"Не удалось отправить письмо на {to} через {config['host']}:{config['port']}: "
                f"{exc.__class__.__name__}: {exc}"
            ) from exc
        logger.info("mail sent backend=%s to=%s subject=%s", self.backend, to, subject)
        return None


MailerFactory = Callable[[], Mailer]

_REGISTRY: dict[str, MailerFactory] = {
    CONSOLE_BACKEND: ConsoleMailer,
    SMTP_BACKEND: SmtpMailer,
}


def get_mailer(backend: str | None = None) -> Mailer:
    name = (backend if backend is not None else settings.mail_backend) or CONSOLE_BACKEND
    factory = _REGISTRY.get(name)
    if factory is None:
        raise MailError(
            f"Неизвестный почтовый бэкенд «{name}». "
            f"Допустимые значения mail_backend: {', '.join(MAIL_BACKENDS)}."
        )
    return factory()
