from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.search.model.search_history import SearchHistory


class SearchHistoryService:

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int, limit: int = 20) -> list[SearchHistory]:
        result = await db.execute(
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def record(
        db: AsyncSession, user_id: int, query: str, filters: dict | None = None, results_count: int = 0
    ) -> SearchHistory:
        entry = SearchHistory(
            user_id=user_id,
            query=query,
            filters=filters,
            results_count=results_count,
        )
        db.add(entry)
        await db.flush()
        return entry
