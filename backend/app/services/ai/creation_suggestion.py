"""根据 RAG 问答结果生成 AI 文化创作推荐参数。"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.ai.rag_service import RAGAnswer, RAGService


@dataclass(frozen=True, slots=True)
class CreationSuggestion:
    """与API Schema解耦的核心层创作推荐结果。"""

    enable: bool
    culture: str = ""
    campus: str = ""
    style: str = ""

    @classmethod
    def disabled(cls) -> "CreationSuggestion":
        return cls(enable=False)


SOURCE_CULTURE_MAP = {
    "01_hongmian.md": "木棉文化",
    "02_lingnan_culture.md": "岭南文化",
    "03_yueju.md": "粤剧文化",
    "04_lingnan_architecture.md": "岭南建筑文化",
    "05_guangzhou_food.md": "广州早茶文化",
    "06_guangzhou_university.md": "广州大学校园文化",
}

REFUSAL_MARKERS = (
    RAGService.FALLBACK_ANSWER,
    "当前知识库没有相关信息，无法准确回答。",
    "该问题不属于小棉的岭南文化知识范围",
)


def build_creation_suggestion(result: RAGAnswer) -> CreationSuggestion:
    if (
        not result.answerable
        or not result.sources
        or any(marker in result.answer for marker in REFUSAL_MARKERS)
    ):
        return CreationSuggestion.disabled()

    primary_source = result.sources[0]
    culture = SOURCE_CULTURE_MAP.get(
        primary_source.source_path,
        primary_source.title.strip(),
    )
    if not culture:
        return CreationSuggestion.disabled()

    return CreationSuggestion(
        enable=True,
        culture=culture,
        campus="广州大学",
        style="国潮风",
    )
