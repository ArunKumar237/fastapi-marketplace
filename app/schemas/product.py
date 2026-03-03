import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.product_image import ProductImageResponse


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)
    category_id: uuid.UUID


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    category_id: uuid.UUID | None = None
    is_active: bool | None = None


class StoreInfo(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class CategoryInfo(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    stock: int
    is_active: bool
    store: StoreInfo
    category: CategoryInfo
    images: list[ProductImageResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    stock: int
    is_active: bool
    store: StoreInfo
    category: CategoryInfo
    images: list[ProductImageResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
