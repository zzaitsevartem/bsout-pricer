from pydantic import BaseModel, Field


class ParserRunRequest(BaseModel):
    store_slug: str = Field(..., min_length=1)
    full_sync: bool = False
    limit: int | None = Field(None, ge=1, le=100000)
    section: str | None = Field(None, min_length=2, max_length=200)


class ParserRunResponse(BaseModel):
    store_slug: str
    status: str
    job_id: str | None = None
    limit: int | None = None
    section: str | None = None


class ParserStatusResponse(BaseModel):
    store_slug: str
    is_running: bool
    last_run: str | None
    products_found: int
    errors: list[str]
