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


class ParserSearchRequest(BaseModel):
    store_slug: str = Field(..., min_length=1, max_length=100)
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(20, ge=1, le=100)


class ParserSearchItemResponse(BaseModel):
    source_sku: str
    title: str
    price_retail: str
    price_opt: str | None = None
    stock_status: str
    url: str


class ParserSearchResponse(BaseModel):
    store_slug: str
    query: str
    found: int
    results: list[ParserSearchItemResponse]
