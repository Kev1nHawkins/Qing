from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import PublishStatus, TaskType
from app.schemas.common import Timestamped


class RouteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=500)
    cover_image_url: str | None = None
    duration_minutes: int = Field(default=60, ge=1)
    distance_km: Decimal = Field(default=0, ge=0)
    status: PublishStatus = PublishStatus.DRAFT


class RouteUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    cover_image_url: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    distance_km: Decimal | None = Field(default=None, ge=0)
    status: PublishStatus | None = None


class RouteRead(Timestamped):
    title: str
    slug: str
    summary: str
    cover_image_url: str | None
    duration_minutes: int
    distance_km: Decimal
    status: str


class TaskCreate(BaseModel):
    route_id: int
    culture_item_id: int | None = None
    location_id: int
    order_no: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=120)
    description: str
    task_type: TaskType = TaskType.CHECK_IN
    question: str | None = None
    options: list[str] | None = None
    correct_answer: str | None = None
    points: int = Field(default=10, ge=0, le=1000)
    qr_code: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    radius_meters: int = Field(default=100, ge=1)


class TaskUpdate(BaseModel):
    culture_item_id: int | None = None
    location_id: int | None = None
    order_no: int | None = Field(default=None, ge=1)
    title: str | None = None
    description: str | None = None
    task_type: TaskType | None = None
    question: str | None = None
    options: list[str] | None = None
    correct_answer: str | None = None
    points: int | None = Field(default=None, ge=0, le=1000)
    qr_code: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    radius_meters: int | None = Field(default=None, ge=1)


class TaskRead(Timestamped):
    route_id: int
    culture_item_id: int | None
    location_id: int
    order_no: int
    title: str
    description: str
    task_type: str
    question: str | None
    options: list[str] | None
    points: int
    qr_code: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    radius_meters: int


class TaskCompleteRequest(BaseModel):
    answer: str | None = None
    qr_code: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None

