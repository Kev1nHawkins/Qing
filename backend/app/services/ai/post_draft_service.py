"""Generate editable community post drafts with a deterministic fallback."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.services.ai.deepseek_llm import DeepSeekLLM
from app.services.ai.llm_service import LLMError


@dataclass(frozen=True)
class PostDraft:
    title: str
    content: str
    tags: list[str]
    provider: str
    model: str
    fallback_used: bool


class PostDraftService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate(self, user_prompt: str) -> PostDraft:
        provider = self.settings.llm_provider.strip().lower()
        if provider == "mock":
            return self._local_draft(user_prompt, fallback_used=False)
        if provider != "deepseek":
            return self._local_draft(user_prompt, fallback_used=True)
        try:
            raw = await DeepSeekLLM.from_settings(self.settings).generate(
                self._build_prompt(user_prompt)
            )
            return self._parse(raw)
        except (LLMError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return self._local_draft(user_prompt, fallback_used=True)

    def _parse(self, raw: str) -> PostDraft:
        cleaned = raw.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        payload: Any = json.loads(fenced.group(1) if fenced else cleaned)
        if not isinstance(payload, dict):
            raise TypeError("Post draft must be an object")
        title = str(payload["title"]).strip()[:120]
        content = str(payload["content"]).strip()[:5000]
        tags = self._tags(payload["tags"])
        if not title or not content:
            raise ValueError("Post draft is empty")
        return PostDraft(
            title=title,
            content=content,
            tags=tags,
            provider="deepseek",
            model=self.settings.deepseek_model,
            fallback_used=False,
        )

    def _local_draft(self, prompt: str, *, fallback_used: bool) -> PostDraft:
        subject = " ".join(prompt.split())
        return PostDraft(
            title=f"我的共创记录｜{subject[:36]}",
            content=(
                f"这次我想分享的主题是：{subject}\n\n"
                "我正在尝试把这份灵感转化为更清晰、更有温度的表达。"
                "欢迎大家一起交流，也期待看到更多不同的创作视角。"
            )[:5000],
            tags=["AI共创", "灵感记录"],
            provider="mock" if not fallback_used else "local-template",
            model="local-post-draft-v1",
            fallback_used=fallback_used,
        )

    @staticmethod
    def _tags(value: Any) -> list[str]:
        if not isinstance(value, list):
            raise TypeError("Post tags must be a list")
        result: list[str] = []
        for item in value:
            tag = str(item).strip().lstrip("#")[:50]
            if tag and tag not in result:
                result.append(tag)
        return result[:10]

    @staticmethod
    def _build_prompt(user_prompt: str) -> str:
        return (
            "你是岭潮共创社区的中文内容编辑。请根据用户意图撰写一份可编辑的社区推文草稿。"
            "不得虚构未经用户提供的活动时间、地点、人物经历或文化史实；不确定的信息使用中性表达。"
            "只输出严格JSON，不要Markdown和额外说明。字段必须为title、content、tags；"
            "title不超过120字，content不超过5000字，tags为不超过10个的字符串数组。\n"
            f"用户要求：{user_prompt}"
        )
