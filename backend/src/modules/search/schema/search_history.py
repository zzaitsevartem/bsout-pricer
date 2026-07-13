from datetime import datetime

from pydantic import BaseModel


class SearchHistoryResponse(BaseModel):
    id: int
    user_id: int
    query: str
    filters: dict | None
    results_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
