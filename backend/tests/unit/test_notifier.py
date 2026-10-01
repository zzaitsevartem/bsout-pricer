import logging
from datetime import datetime, timezone
from decimal import Decimal

import pytest

import src.db_metadata  # noqa: F401
from src.modules.tracking.model.tracking import Notification
from src.modules.tracking.service.notifier import (
    DEFAULT_CHANNEL,
    InAppNotifier,
    LoggingNotifier,
    Notifier,
    NotifierError,
    NotifierNotConfiguredError,
    configured_channels,
    get_notifier,
    register_notifier,
    unregister_notifier,
)

pytestmark = pytest.mark.unit


def _notification(channel: str = DEFAULT_CHANNEL) -> Notification:
    return Notification(
        user_id=1,
        tracked_product_id=2,
        product_id=3,
        type="price_drop",
        channel=channel,
        status="pending",
        title="Цена снизилась",
        body="Дисплей подешевел",
        old_price=Decimal("2000.00"),
        new_price=Decimal("1500.00"),
        dedup_key="tp2:price_drop:1500.00",
        error="предыдущая ошибка",
    )


@pytest.fixture(autouse=True)
def _clean_registry():
    yield
    unregister_notifier("email")
    unregister_notifier("telegram")


def test_default_channel_is_in_app():
    assert DEFAULT_CHANNEL == "in_app"
    assert configured_channels() == ("in_app",)


def test_factory_returns_in_app_notifier_by_default():
    assert isinstance(get_notifier(), InAppNotifier)
    assert isinstance(get_notifier("in_app"), InAppNotifier)


async def test_in_app_notifier_marks_notification_sent():
    notification = _notification()
    before = datetime.now(timezone.utc)

    result = await get_notifier(notification.channel).send(notification)

    assert result is notification
    assert notification.status == "sent"
    assert notification.error is None
    assert notification.sent_at is not None
    assert notification.sent_at >= before


async def test_logging_notifier_marks_sent_and_logs(caplog):
    notification = _notification()
    notifier = LoggingNotifier("telegram")

    with caplog.at_level(logging.INFO, logger="bscout.notifications"):
        await notifier.send(notification)

    assert notification.status == "sent"
    assert notification.sent_at is not None
    assert any("tp2:price_drop:1500.00" in record.getMessage() for record in caplog.records)


@pytest.mark.parametrize("channel", ["email", "telegram"])
def test_known_but_unconfigured_channel_raises_clear_error(channel):
    with pytest.raises(NotifierNotConfiguredError) as exc_info:
        get_notifier(channel)

    message = str(exc_info.value)
    assert channel in message
    assert "register_notifier" in message


def test_unknown_channel_raises_clear_error():
    with pytest.raises(NotifierNotConfiguredError) as exc_info:
        get_notifier("carrier_pigeon")

    message = str(exc_info.value)
    assert "carrier_pigeon" in message
    assert "in_app" in message


def test_not_configured_error_is_a_notifier_error():
    assert issubclass(NotifierNotConfiguredError, NotifierError)


async def test_registered_channel_becomes_available():
    register_notifier("telegram", lambda: LoggingNotifier("telegram"))

    notifier = get_notifier("telegram")
    assert isinstance(notifier, LoggingNotifier)
    assert notifier.channel == "telegram"
    assert set(configured_channels()) == {"in_app", "telegram"}

    notification = _notification("telegram")
    await notifier.send(notification)
    assert notification.status == "sent"


def test_register_rejects_channel_outside_model_enum():
    with pytest.raises(NotifierError):
        register_notifier("sms", InAppNotifier)

    assert "sms" not in configured_channels()


def test_default_channel_cannot_be_unregistered():
    unregister_notifier(DEFAULT_CHANNEL)

    assert isinstance(get_notifier(DEFAULT_CHANNEL), InAppNotifier)


def test_notifier_is_abstract():
    with pytest.raises(TypeError):
        Notifier()
