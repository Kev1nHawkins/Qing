"""Structured poster copy generation with explicit provider/fallback metadata."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.services.ai.deepseek_llm import DeepSeekLLM
from app.services.ai.llm_service import LLMError


@dataclass(frozen=True)
class CreationContent:
    title: str
    subtitle: str
    cultural_description: str
    visual_prompt: str
    tags: list[str]
    suggested_palette: list[str]
    layout_hint: str
    text_provider: str
    text_model: str
    fallback_used: bool

    def metadata(self) -> dict[str, Any]:
        return asdict(self)


class CreationContentService:
    """Generate structured copy; use deterministic local copy when LLM is disabled."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate(
        self,
        *,
        base_prompt: str,
        options: dict[str, Any],
    ) -> CreationContent:
        provider = self.settings.llm_provider.strip().lower()
        if provider == "mock":
            return self._local_content(options, fallback_used=False)
        if provider != "deepseek":
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.settings.llm_provider}")

        try:
            adapter = DeepSeekLLM.from_settings(self.settings)
            raw = await adapter.generate(self._deepseek_prompt(base_prompt, options))
            return self._parse_deepseek(raw)
        except (LLMError, ValueError, json.JSONDecodeError, TypeError, KeyError):
            return self._local_content(options, fallback_used=True)

    def _parse_deepseek(self, raw: str) -> CreationContent:
        cleaned = raw.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        payload = json.loads(fenced.group(1) if fenced else cleaned)
        required = (
            "title",
            "subtitle",
            "culturalDescription",
            "visualPrompt",
            "tags",
            "suggestedPalette",
            "layoutHint",
        )
        if any(key not in payload for key in required):
            raise KeyError("DeepSeek creation JSON is incomplete")
        return CreationContent(
            title=str(payload["title"]).strip()[:120],
            subtitle=str(payload["subtitle"]).strip()[:160],
            cultural_description=str(payload["culturalDescription"]).strip()[:1000],
            visual_prompt=str(payload["visualPrompt"]).strip()[:3000],
            tags=self._string_list(payload["tags"], limit=8),
            suggested_palette=self._string_list(payload["suggestedPalette"], limit=6),
            layout_hint=str(payload["layoutHint"]).strip()[:500],
            text_provider="deepseek",
            text_model=self.settings.deepseek_model,
            fallback_used=False,
        )

    def _local_content(
        self,
        options: dict[str, Any],
        *,
        fallback_used: bool,
    ) -> CreationContent:
        culture = str(options.get("culture_element") or "岭南文化")
        campus = str(options.get("campus_landmark") or "广州大学")
        style = str(options.get("style") or "国潮")
        palette_map = {
            "剪纸": ["#a51f2d", "#f6dfbd", "#7a171f"],
            "现代插画": ["#1f6654", "#d9eee4", "#e2a53b"],
            "国潮": ["#9b2634", "#e8b44f", "#173f35"],
        }
        return CreationContent(
            title=f"{culture}入校园",
            subtitle=f"在{campus}遇见{culture}",
            cultural_description=(
                f"以{culture}连接广州城市记忆与{campus}校园生活，"
                f"用{style}视觉语言完成一次青年文化表达。"
            ),
            visual_prompt=(
                f"竖版文化海报，主题为{culture}，场景明确表现{campus}，"
                f"采用{style}风格，包含岭南纹样、清晰中文标题和校园空间层次。"
            ),
            tags=[culture, campus, style, "岭南文化", "校园共创"],
            suggested_palette=palette_map.get(style, palette_map["国潮"]),
            layout_hint=f"{style}竖版构图，地标作为主体，文化元素作为前景符号",
            text_provider="local-template",
            text_model="local-structured-v1",
            fallback_used=fallback_used,
        )

    @staticmethod
    def _string_list(value: Any, *, limit: int) -> list[str]:
        if not isinstance(value, list):
            raise TypeError("Expected a list")
        return [str(item).strip() for item in value if str(item).strip()][:limit]

    @staticmethod
    def _deepseek_prompt(base_prompt: str, options: dict[str, Any]) -> str:
        return (
            "你是岭南文化海报策划师。根据以下基础Prompt和选项生成严格JSON，"
            "不要输出Markdown或额外说明。JSON字段必须为title、subtitle、"
            "culturalDescription、visualPrompt、tags、suggestedPalette、layoutHint。\n"
            f"基础Prompt：{base_prompt}\n"
            f"用户选项：{json.dumps(options, ensure_ascii=False)}"
        )
