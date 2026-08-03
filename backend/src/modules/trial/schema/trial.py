from pydantic import BaseModel, Field

from src.modules.products.schema.product import ProductResponse


class TrialStatusResponse(BaseModel):
    available: bool
    client_id: str


class TrialSearchRequest(BaseModel):
    query: str = Field(default="", max_length=500)


class TrialSearchResponse(BaseModel):
    results: list[ProductResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    query: str = ""
