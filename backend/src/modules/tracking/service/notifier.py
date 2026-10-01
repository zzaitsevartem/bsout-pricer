import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timezone

from src.modules.tracking.model.tracking import NOTIFICATION_CHANNELS, Notification

DEFAULT_CHANNEL = "in_app"

logger = logging.getLogger("bscout.notifications")


class NotifierError(RuntimeError):
    pass


class NotifierNotConfiguredError(NotifierError):
    pass


class Notifier(ABC):
    channel: str = DEFAULT_CHANNEL

    @abstractmethod
    async def send(self, notification: Notification) -> Notification: ...

    def mark_sent(self, notification: Notification) -> Notification:
        notification.status = "sent"
        notification.sent_at = datetime.now(timezone.utc)
        notification.error = None
        return notification


class InAppNotifier(Notifier):
    channel = DEFAULT_CHANNEL

    async def send(self, notification: Notification) -> Notification:
        return self.mark_sent(notification)


class LoggingNotifier(Notifier):
    def __init__(self, channel: str = DEFAULT_CHANNEL) -> None:
        self.channel = channel

    async def send(self, notification: Notification) -> Notification:
        logger.info(
            "notification channel=%s user=%s type=%s dedup=%s old=%s new=%s",
            self.channel,
            notification.user_id,
            notification.type,
            notification.dedup_key,
            notification.old_price,
            notification.new_price,
        )
        return self.mark_sent(notification)


NotifierFactory = Callable[[], Notifier]

_REGISTRY: dict[str, NotifierFactory] = {DEFAULT_CHANNEL: InAppNotifier}


def configured_channels() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def register_notifier(channel: str, factory: NotifierFactory) -> None:
    if channel not in NOTIFICATION_CHANNELS:
        raise NotifierError(
            f"Неизвестный канал доставки «{channel}». "
            f"Допустимые каналы: {', '.join(NOTIFICATION_CHANNELS)}."
        )
    _REGISTRY[channel] = factory


def unregister_notifier(channel: str) -> None:
    if channel != DEFAULT_CHANNEL:
        _REGISTRY.pop(channel, None)


def get_notifier(channel: str = DEFAULT_CHANNEL) -> Notifier:
    factory = _REGISTRY.get(channel)
    if factory is not None:
        return factory()
    if channel in NOTIFICATION_CHANNELS:
        raise NotifierNotConfiguredError(
            f"Канал доставки «{channel}» ещё не настроен. "
            f"Зарегистрируйте реализацию через register_notifier({channel!r}, ...). "
            f"Настроены: {', '.join(configured_channels())}."
        )
    raise NotifierNotConfiguredError(
        f"Неизвестный канал доставки «{channel}». "
        f"Допустимые каналы: {', '.join(NOTIFICATION_CHANNELS)}."
    )
