from pydantic import BaseModel, Field

from app.models.enums import PublishStatus
from app.schemas.common import Timestamped


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=80)
    description: str = Field(max_length=500)
    prompt_template: str
    options_schema: dict | None = None
    preview_url: str | None = None
    status: PublishStatus = PublishStatus.DRAFT
    culture_item_id: int | None = None


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    prompt_template: str | None = None
    options_schema: dict | None = None
    preview_url: str | None = None
    status: PublishStatus | None = None
    culture_item_id: int | None = None


class TemplateRead(Timestamped):
    name: str
    code: str
    description: str
    prompt_template: str
    options_schema: dict | None
    preview_url: str | None
    status: str
    culture_item_id: int | None


class CreationRequest(BaseModel):
    template_id: int
    culture_item_id: int | None = None
    title: str = Field(min_length=1, max_length=120)
    options: dict = Field(default_factory=dict)


class CreationRead(Timestamped):
    user_id: int
    template_id: int
    culture_item_id: int | None
    title: str
    prompt: str
    input_payload: dict
    output_url: str | None
    description: str | None
    status: str
    error_message: str | None
    retry_count: int

