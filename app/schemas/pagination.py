import math
from typing import Generic, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int = 0

    @model_validator(mode="after")
    def compute_pages(self):
        self.pages = math.ceil(self.total / self.size) if self.size > 0 else 0
        return self
