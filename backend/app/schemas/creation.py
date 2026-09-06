from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from app.models.enums import PublishStatus
from app.schemas.common import Timestamped
from app.services.creation.template_validation import (
    normalize_options_schema,
    validate_template_contract,
)


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    prompt_template: str = Field(min_length=1)
    options_schema: dict[str, list[str]]
    preview_url: str | None = None
    status: PublishStatus = PublishStatus.DRAFT
    culture_item_id: int | None = None

    @field_validator("name", "code", "description", "prompt_template")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("字段不能为空")
        return cleaned

    @field_validator("options_schema", mode="before")
    @classmethod
    def validate_options(cls, value: object) -> dict[str, list[str]]:
        return normalize_options_schema(value)

    @model_validator(mode="after")
    def validate_prompt_options(self) -> "TemplateCreate":
        validate_template_contract(self.prompt_template, self.options_schema)
        return self


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    prompt_template: str | None = None
    options_schema: dict[str, list[str]] | None = None
    preview_url: str | None = None
    status: PublishStatus | None = None
    culture_item_id: int | None = None

    @field_validator("name", "description", "prompt_template")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("字段不能为空")
        return cleaned

    @field_validator("options_schema", mode="before")
    @classmethod
    def validate_options(cls, value: object) -> dict[str, list[str]] | None:
        if value is None:
            return None
        return normalize_options_schema(value)


class TemplateRead(Timestamped):
    name: str
    code: str
    description: str
    prompt_template: str
    options_schema: dict[str, list[str]] | None
    preview_url: str | None
    status: str
    culture_item_id: int | None


class CreationRequest(BaseModel):
    template_id: int
    culture_item_id: int | None = None
    title: str = Field(min_length=1, max_length=120)
    options: dict = Field(default_factory=dict)


class FreeImageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    aspect_ratio: str = Field(alias="aspectRatio", pattern=r"^(SQUARE|PORTRAIT|LANDSCAPE)$")

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("提示词不能为空")
        return cleaned


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
