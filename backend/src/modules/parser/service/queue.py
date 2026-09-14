import asyncio

from src.celery_app import celery_app

PARSER_QUEUE_JOB = "run_parser"


async def enqueue_parser_run(
    store_slug: str,
    full_sync: bool,
    limit: int | None,
    section: str | None = None,
) -> str | None:
    result = await asyncio.to_thread(
        celery_app.send_task,
        PARSER_QUEUE_JOB,
        args=[store_slug, full_sync, limit, section],
    )
    return result.id
