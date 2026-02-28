import uuid

from pydantic import BaseModel, Field


class StoreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    product_count: int = Field(default=0, ge=0)


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    product_count: int | None = Field(default=None, ge=0)


class StoreStatusUpdate(BaseModel):
    is_active: bool


class StoreOwnerInfo(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class StoreResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    owner_id: uuid.UUID
    owner: StoreOwnerInfo
    product_count: int

    model_config = {"from_attributes": True}


class StoreListResponse(BaseModel):
    page: int
    size: int
    total: int
    items: list[StoreResponse]
