from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, alias="pageSize", ge=1, le=100)


class PageData(BaseModel, Generic[T]):
    total: int
    items: list[T]
    page: int
    page_size: int = Field(alias="pageSize")


class Timestamped(ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime

