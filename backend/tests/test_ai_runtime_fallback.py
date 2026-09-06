from pathlib import Path

import pytest

from app.services.ai.keyword_retriever import (
    KeywordKnowledgeRetriever,
    ResilientKnowledgeRetriever,
)
from app.services.ai.llm_service import LLMAdapter, LLMNetworkError, LLMService, MockLLM
from app.services.ai.rag_service import RAGService


ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "data" / "knowledge_base"
PROMPT = ROOT / "data" / "prompts" / "rag_chat.txt"


class FailingRetriever:
    def retrieve(self, query: str, top_k: int = 5):
        raise RuntimeError("embedding unavailable")


class TimeoutLLM(LLMAdapter):
    async def generate(self, prompt: str) -> str:
        raise LLMNetworkError("timeout")


class SuccessLLM(LLMAdapter):
    async def generate(self, prompt: str) -> str:
        return "基于本地知识来源生成的模型回答。"


class VectorRetriever:
    last_mode = "vector"

    def retrieve(self, query: str, top_k: int = 5):
        return [
            {
                "text": "木棉是广州市花。",
                "metadata": {
                    "source_path": "01_hongmian.md",
                    "title": "木棉文化",
                    "section": "简介",
                },
                "score": 0.9,
            }
        ]


class LowConfidenceKeywordRetriever:
    last_mode = "keyword"

    def retrieve(self, query: str, top_k: int = 5):
        return [
            {
                "text": "木棉是广州市花。",
                "metadata": {
                    "source_path": "01_hongmian.md",
                    "title": "木棉文化",
                    "section": "简介",
                },
                "score": 0.64,
            }
        ]


def build_service(*, deepseek: bool = False) -> RAGService:
    keyword = KeywordKnowledgeRetriever(KNOWLEDGE)
    retriever = ResilientKnowledgeRetriever(FailingRetriever(), keyword)
    fallback = LLMService(MockLLM(), PROMPT)
    external = LLMService(TimeoutLLM(), PROMPT) if deepseek else fallback
    return RAGService(
        retriever=retriever,
        llm_service=external,
        fallback_llm_service=fallback,
        external_provider="deepseek" if deepseek else None,
        external_model="configured-model" if deepseek else None,
        min_score=0.45,
    )


@pytest.mark.asyncio
async def test_missing_vector_runtime_uses_keyword_and_preset() -> None:
    result = await build_service().answer("为什么木棉是广州的象征？")
    assert result.answerable is True
    assert result.answer
    assert result.sources
    assert result.mode == "PRESET_FALLBACK"
    assert result.provider == "preset"
    assert result.fallback_used is True


@pytest.mark.asyncio
async def test_deepseek_timeout_uses_grounded_preset() -> None:
    result = await build_service(deepseek=True).answer("广州大学的校训是什么？")
    assert "博学笃行" in result.answer
    assert result.mode == "PRESET_FALLBACK"
    assert result.fallback_used is True
    assert result.sources


@pytest.mark.asyncio
async def test_unknown_question_is_not_fabricated() -> None:
    result = await build_service().answer("量子计算机如何维修主板？")
    assert result.answerable is False
    assert result.answer == RAGService.FALLBACK_ANSWER
    assert result.sources == []


@pytest.mark.asyncio
async def test_unknown_question_uses_general_deepseek_when_configured() -> None:
    keyword = KeywordKnowledgeRetriever(KNOWLEDGE)
    retriever = ResilientKnowledgeRetriever(None, keyword)
    fallback = LLMService(MockLLM(), PROMPT)
    result = await RAGService(
        retriever=retriever,
        llm_service=LLMService(SuccessLLM(), PROMPT),
        fallback_llm_service=fallback,
        external_provider="deepseek",
        external_model="configured-model",
    ).answer("请介绍太阳系的八大行星。")
    assert result.answerable is True
    assert result.answer
    assert result.sources == []
    assert result.mode == "GENERAL_DEEPSEEK"
    assert result.provider == "deepseek"
    assert result.fallback_used is False


@pytest.mark.asyncio
async def test_low_confidence_keyword_match_uses_general_deepseek() -> None:
    fallback = LLMService(MockLLM(), PROMPT)
    result = await RAGService(
        retriever=LowConfidenceKeywordRetriever(),
        llm_service=LLMService(SuccessLLM(), PROMPT),
        fallback_llm_service=fallback,
        external_provider="deepseek",
        external_model="configured-model",
    ).answer("请问你背后的开发团队是什么？")
    assert result.answerable is True
    assert result.sources == []
    assert result.mode == "GENERAL_DEEPSEEK"
    assert result.provider == "deepseek"
    assert result.fallback_used is False


@pytest.mark.asyncio
async def test_unknown_question_keeps_safe_fallback_when_general_deepseek_times_out() -> None:
    result = await build_service(deepseek=True).answer("请介绍太阳系的八大行星。")
    assert result.answerable is False
    assert result.answer == RAGService.FALLBACK_ANSWER
    assert result.mode == "PRESET_FALLBACK"
    assert result.fallback_used is True


@pytest.mark.asyncio
async def test_keyword_deepseek_mode_when_external_adapter_succeeds() -> None:
    keyword = KeywordKnowledgeRetriever(KNOWLEDGE)
    retriever = ResilientKnowledgeRetriever(None, keyword)
    fallback = LLMService(MockLLM(), PROMPT)
    result = await RAGService(
        retriever=retriever,
        llm_service=LLMService(SuccessLLM(), PROMPT),
        fallback_llm_service=fallback,
        external_provider="deepseek",
        external_model="configured-model",
    ).answer("为什么木棉是广州的象征？")
    assert result.mode == "KEYWORD_DEEPSEEK"
    assert result.provider == "deepseek"
    assert result.fallback_used is False


@pytest.mark.asyncio
async def test_rag_deepseek_mode_when_vector_and_external_succeed() -> None:
    fallback = LLMService(MockLLM(), PROMPT)
    result = await RAGService(
        retriever=VectorRetriever(),
        llm_service=LLMService(SuccessLLM(), PROMPT),
        fallback_llm_service=fallback,
        external_provider="deepseek",
        external_model="configured-model",
    ).answer("木棉是什么？")
    assert result.mode == "RAG_DEEPSEEK"
    assert result.provider == "deepseek"
    assert result.fallback_used is False
