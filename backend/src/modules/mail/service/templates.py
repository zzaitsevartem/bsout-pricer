from dataclasses import dataclass
from urllib.parse import quote

from src.config import settings

PASSWORD_RESET_PATH = "/reset-password"
PASSWORD_RESET_SUBJECT = "BScout: восстановление пароля"
PASSWORD_CHANGED_SUBJECT = "BScout: пароль изменён"

RESET_TOKEN_TTL_HOURS = 1


@dataclass(frozen=True)
class MailMessage:
    subject: str
    text: str
    html: str


def frontend_link(path: str, **params: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}"
    query = "&".join(f"{key}={quote(value, safe='')}" for key, value in params.items())
    return f"{base}{suffix}?{query}" if query else f"{base}{suffix}"


def password_reset_link(token: str) -> str:
    return frontend_link(PASSWORD_RESET_PATH, token=token)


def password_reset_message(token: str) -> MailMessage:
    link = password_reset_link(token)
    text = (
        "Здравствуйте!\n\n"
        "Вы запросили восстановление пароля в BScout. "
        f"Перейдите по ссылке, чтобы задать новый пароль:\n{link}\n\n"
        f"Ссылка действует {RESET_TOKEN_TTL_HOURS} час и может быть использована один раз.\n"
        "Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо — "
        "пароль останется прежним.\n"
    )
    html = (
        "<p>Здравствуйте!</p>"
        "<p>Вы запросили восстановление пароля в BScout. "
        f'Перейдите по ссылке, чтобы задать новый пароль:<br><a href="{link}">{link}</a></p>'
        f"<p>Ссылка действует {RESET_TOKEN_TTL_HOURS} час и может быть использована один раз.</p>"
        "<p>Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо — "
        "пароль останется прежним.</p>"
    )
    return MailMessage(subject=PASSWORD_RESET_SUBJECT, text=text, html=html)


def password_changed_message() -> MailMessage:
    text = (
        "Здравствуйте!\n\n"
        "Пароль от вашего аккаунта BScout был изменён. "
        "Все остальные сеансы завершены.\n"
        "Если это были не вы, немедленно восстановите пароль: "
        f"{frontend_link(PASSWORD_RESET_PATH)}\n"
    )
    html = (
        "<p>Здравствуйте!</p>"
        "<p>Пароль от вашего аккаунта BScout был изменён. Все остальные сеансы завершены.</p>"
        "<p>Если это были не вы, немедленно восстановите пароль: "
        f'<a href="{frontend_link(PASSWORD_RESET_PATH)}">восстановление пароля</a>.</p>'
    )
    return MailMessage(subject=PASSWORD_CHANGED_SUBJECT, text=text, html=html)
