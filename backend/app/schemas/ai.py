"""AI文化知识问答接口模型。"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


QuestionText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=500),
]


class AIChatRequest(BaseModel):
    """AI文化知识问答请求。"""

    question: QuestionText = Field(
        description="用户提出的岭南文化或广州大学校园文化问题",
        examples=["为什么木棉是广州的象征？"],
    )


class AIChatSource(BaseModel):
    """回答实际引用的知识库来源。"""

    source_path: str
    title: str
    section: str
    score: float = Field(ge=-1, le=1)


class CreationSuggestionRead(BaseModel):
    """问答结束后可选的AI文化创作参数。"""

    enable: bool
    culture: str
    campus: str
    style: str


class AIChatData(BaseModel):
    answer: str
    sources: list[AIChatSource]
    creation_suggestion: CreationSuggestionRead
