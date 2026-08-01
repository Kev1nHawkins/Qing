"""RAG 检索与问答生成编排服务。"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Protocol

from app.services.ai.llm_service import LLMService


logger = logging.getLogger(__name__)


class Retriever(Protocol):
    """RAG 服务所需的 Retriever 最小接口，便于测试替换。"""

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]: ...


@dataclass(frozen=True, slots=True)
class RAGSource:
    source_path: str
    title: str
    section: str
    score: float


@dataclass(frozen=True, slots=True)
class RAGAnswer:
    question: str
    answer: str
    answerable: bool
    sources: list[RAGSource]
    mode: str = "PRESET_FALLBACK"
    provider: str = "preset"
    model: str = "local-knowledge"
    fallback_used: bool = True


class RAGService:
    """执行“检索 → 上下文拼接 → LLM生成”的完整流程。"""

    FALLBACK_ANSWER = "当前知识库中暂未找到足够可靠的相关资料，你可以换一种问法。"

    def __init__(
        self,
        retriever: Retriever,
        llm_service: LLMService,
        top_k: int = 5,
        min_score: float = 0.45,
        fallback_llm_service: LLMService | None = None,
        external_provider: str | None = None,
        external_model: str | None = None,
    ) -> None:
        if top_k < 1:
            raise ValueError("top_k必须大于0")
        if not 0 <= min_score <= 1:
            raise ValueError("min_score必须位于0到1之间")
        self.retriever = retriever
        self.llm_service = llm_service
        self.top_k = top_k
        self.min_score = min_score
        self.fallback_llm_service = fallback_llm_service or llm_service
        self.external_provider = external_provider
        self.external_model = external_model

    async def answer(self, question: str) -> RAGAnswer:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("问题不能为空")

        try:
            retrieved = self.retriever.retrieve(clean_question, top_k=self.top_k)
        except Exception as exc:
            logger.warning("Knowledge retrieval failed; returning safe fallback: %s", type(exc).__name__)
            retrieved = []
        qualified = [
            item for item in retrieved if float(item.get("score", 0.0)) >= self.min_score
        ]
        if not qualified:
            return RAGAnswer(clean_question, self.FALLBACK_ANSWER, False, [])

        context = self._build_context(qualified)
        sources = [
            RAGSource(
                source_path=str(item["metadata"].get("source_path", "")),
                title=str(item["metadata"].get("title", "")),
                section=str(item["metadata"].get("section", "")),
                score=float(item["score"]),
            )
            for item in qualified
        ]
        retrieval_mode = getattr(self.retriever, "last_mode", "vector")
        if self.external_provider:
            try:
                answer = await self.llm_service.answer(clean_question, context)
                mode = (
                    "RAG_DEEPSEEK"
                    if retrieval_mode == "vector"
                    else "KEYWORD_DEEPSEEK"
                )
                return RAGAnswer(
                    clean_question,
                    answer,
                    True,
                    sources,
                    mode=mode,
                    provider=self.external_provider,
                    model=self.external_model or "",
                    fallback_used=False,
                )
            except Exception as exc:
                logger.warning(
                    "External LLM unavailable; using preset fallback: %s",
                    type(exc).__name__,
                )

        answer = await self.fallback_llm_service.answer(clean_question, context)
        return RAGAnswer(
            clean_question,
            answer,
            True,
            sources,
            mode="PRESET_FALLBACK",
            provider="preset",
            model="local-knowledge",
            fallback_used=True,
        )

    @staticmethod
    def _build_context(results: list[dict[str, Any]]) -> str:
        blocks: list[str] = []
        for index, item in enumerate(results, start=1):
            metadata = item.get("metadata") or {}
            label = (
                f"[资料{index} | 来源: {metadata.get('source_path', '未知')}"
                f" | 章节: {metadata.get('section', '未知')}]"
            )
            blocks.append(f"{label}\n{item.get('text', '').strip()}")
        return "\n\n".join(blocks)
