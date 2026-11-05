from pydantic import BaseModel, Field, HttpUrl


class DeviceImage(BaseModel):
    url: HttpUrl
    source_name: str = Field(min_length=1)
    source_url: HttpUrl
    license: str | None = None
    attribution: str | None = None


class DeviceBrand(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class DeviceDetail(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: int
    model_key: str
    name: str
    brand: DeviceBrand
    aliases: list[str]
    model_codes: list[str]
    release_year: int | None
    images: list[DeviceImage]
    metadata_source_url: str | None


class DeviceMetadata(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_key: str = Field(min_length=1)
    release_year: int | None = Field(default=None, ge=1970, le=2100)
    model_codes: list[str] = Field(default_factory=list)
    images: list[DeviceImage] = Field(default_factory=list)
    metadata_source_url: HttpUrl
