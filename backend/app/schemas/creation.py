from typing import Any

from pydantic import BaseModel, Field, computed_field

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

    def _generation(self) -> dict[str, Any]:
        value = self.input_payload.get("_generation")
        return value if isinstance(value, dict) else {}

    @computed_field
    @property
    def creationId(self) -> int:
        return self.id

    @computed_field
    @property
    def resultUrl(self) -> str | None:
        return self.output_url

    @computed_field
    @property
    def thumbnailUrl(self) -> str | None:
        return self.output_url

    @computed_field
    @property
    def templateId(self) -> int:
        return self.template_id

    @computed_field
    @property
    def cultureItemId(self) -> int | None:
        return self.culture_item_id

    @computed_field
    @property
    def provider(self) -> str:
        return str(self._generation().get("provider") or "unknown")

    @computed_field
    @property
    def generationMode(self) -> str:
        return str(self._generation().get("generationMode") or "UNKNOWN")

    @computed_field
    @property
    def model(self) -> str:
        return str(self._generation().get("model") or "unknown")

    @computed_field
    @property
    def imageSource(self) -> str:
        return str(self._generation().get("imageSource") or "unknown")

    @computed_field
    @property
    def fallbackUsed(self) -> bool:
        return bool(self._generation().get("fallbackUsed", False))

    @computed_field
    @property
    def visualPrompt(self) -> str:
        return str(self._generation().get("visualPrompt") or self.prompt)

    @computed_field
    @property
    def tags(self) -> list[str]:
        value = self._generation().get("tags")
        return [str(item) for item in value] if isinstance(value, list) else []
