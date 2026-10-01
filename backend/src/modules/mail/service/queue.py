import asyncio
import logging
import os
from collections.abc import Awaitable, Callable

from src.celery_app import celery_app
from src.config import settings

logger = logging.getLogger("bscout.mail")

MAIL_QUEUE_JOB = "send_password_mail"
MAIL_QUEUE_ENV_FLAG = "MAIL_QUEUE_ENABLED"
TRUTHY_VALUES = ("1", "true", "yes", "on")

MailDeliver = Callable[[str, str, str, str | None], Awaitable[None]]

_pending: set[asyncio.Task] = set()


def queue_enabled() -> bool:
    flag = getattr(settings, "mail_queue_enabled", None)
    if flag is None:
        flag = os.getenv(MAIL_QUEUE_ENV_FLAG, "")
    return str(flag).strip().lower() in TRUTHY_VALUES


async def _enqueue(to: str, subject: str, text: str, html: str | None) -> bool:
    if not queue_enabled():
        return False
    try:
        await asyncio.to_thread(
            celery_app.send_task, MAIL_QUEUE_JOB, args=[to, subject, text, html]
        )
    except Exception:
        logger.exception("mail queue unavailable, delivering in background instead")
        return False
    return True


def _prune() -> None:
    for task in tuple(_pending):
        if task.done() or task.get_loop().is_closed():
            _pending.discard(task)


async def _spawn(deliver: MailDeliver, to: str, subject: str, text: str, html: str | None) -> None:
    _prune()
    task = asyncio.create_task(deliver(to, subject, text, html))
    _pending.add(task)
    task.add_done_callback(_pending.discard)
    await asyncio.sleep(0)


async def dispatch_mail(
    deliver: MailDeliver,
    to: str,
    subject: str,
    text: str,
    html: str | None = None,
) -> None:
    if await _enqueue(to, subject, text, html):
        return
    await _spawn(deliver, to, subject, text, html)


async def drain_pending_mail() -> None:
    loop = asyncio.get_running_loop()
    while True:
        _prune()
        current = tuple(task for task in _pending if task.get_loop() is loop)
        if not current:
            return
        await asyncio.gather(*current, return_exceptions=True)
