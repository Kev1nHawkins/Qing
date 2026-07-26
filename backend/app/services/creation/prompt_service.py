"""将Qing创作模板与AI图片Prompt模板合并。"""

from collections.abc import Mapping
from typing import Any

from app.services.creation.prompt_builder import ImagePromptBuilder


class CreationPromptService:
    def __init__(self, image_prompt_builder: ImagePromptBuilder | None = None) -> None:
        self.image_prompt_builder = image_prompt_builder or ImagePromptBuilder()

    def build(self, template: str, options: Mapping[str, Any]) -> str:
        """保留数据库模板约束，并为标准海报参数增加完整图片Prompt。"""
        template_prompt = template.format(**options).strip()
        culture = options.get("culture_element") or options.get("culture")
        campus = options.get("campus_landmark") or options.get("campus")
        style = options.get("style")
        if not all(isinstance(value, str) and value.strip() for value in (culture, campus, style)):
            return template_prompt

        image_prompt = self.image_prompt_builder.build(
            culture=culture.strip(),
            campus=campus.strip(),
            style=style.strip(),
        ).strip()
        return f"{image_prompt}\n\n创作模板补充要求：{template_prompt}"
