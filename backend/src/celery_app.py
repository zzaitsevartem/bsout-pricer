from celery import Celery
from celery.schedules import crontab

from src.config import settings

celery_app = Celery("bscout", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    task_events=True,
    task_ignore_result=True,
)

celery_app.conf.beat_schedule = {
    "sync_catalog_daily": {
        "task": "sync_catalog",
        "schedule": crontab(hour=3, minute=0),
    },
    "sync_prices_daily_three_runs": {
        "task": "sync_prices",
        "schedule": crontab(hour="7,13,19", minute=30),
    },
    "expire_subscriptions_hourly": {
        "task": "expire_subscriptions",
        "schedule": crontab(minute=5),
    },
    "cleanup_refresh_tokens_daily": {
        "task": "cleanup_refresh_tokens",
        "schedule": crontab(hour=4, minute=30),
    },
    "prune_history_weekly": {
        "task": "prune_history",
        "schedule": crontab(hour=4, minute=45, day_of_week="sun"),
    },
}
