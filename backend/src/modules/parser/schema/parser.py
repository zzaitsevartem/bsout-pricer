from pydantic import BaseModel, Field


class ParserRunRequest(BaseModel):
    store_slug: str = Field(..., min_length=1)
    full_sync: bool = False


class ParserStatusResponse(BaseModel):
    store_slug: str
    is_running: bool
    last_run: str | None
    products_found: int
    errors: list[str]
