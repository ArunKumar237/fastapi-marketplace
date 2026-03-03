import uuid
from datetime import datetime

from pydantic import BaseModel


class ProductImageResponse(BaseModel):
    id: uuid.UUID
    image_url: str
    is_primary: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
