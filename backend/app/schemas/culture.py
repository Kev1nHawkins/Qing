from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import PublishStatus
from app.schemas.common import Timestamped


class CultureCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    cover_image_url: str | None = None
    source_title: str = Field(min_length=1, max_length=255)
    source_url: str | None = None
    status: PublishStatus = PublishStatus.DRAFT


class CultureUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = None
    summary: str | None = None
    content: str | None = None
    cover_image_url: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    status: PublishStatus | None = None


class CultureRead(Timestamped):
    title: str
    slug: str
    category: str
    summary: str
    content: str
    cover_image_url: str | None
    source_title: str
    source_url: str | None
    status: str


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=255)
    description: str | None = None
    latitude: Decimal
    longitude: Decimal
    image_url: str | None = None
    culture_item_id: int | None = None


class LocationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    description: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    image_url: str | None = None
    culture_item_id: int | None = None


class LocationRead(Timestamped):
    name: str
    address: str
    description: str | None
    latitude: Decimal
    longitude: Decimal
    image_url: str | None
    culture_item_id: int | None

