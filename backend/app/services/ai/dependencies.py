"""AI服务依赖装配；HTTP层只依赖RAGService公开接口。"""

from __future__ import annotations

from functools import lru_cache
import logging
from pathlib import Path

from app.core.config import Settings, get_settings
from app.services.ai.deepseek_llm import DeepSeekLLM
from app.services.ai.llm_service import (
    LLMAdapter,
    LLMConfigurationError,
    LLMService,
    MockLLM,
)
from app.services.ai.rag_service import RAGService
from app.services.ai.retriever import KnowledgeRetriever
from app.services.ai.keyword_retriever import (
    KeywordKnowledgeRetriever,
    ResilientKnowledgeRetriever,
)


BACKEND_ROOT = Path(__file__).resolve().parents[3]
REPOSITORY_ROOT = BACKEND_ROOT.parent
logger = logging.getLogger(__name__)


def _resolve_path(configured_path: str, *, prefer_repository: bool = False) -> Path:
    path = Path(configured_path)
    if path.is_absolute():
        return path

    candidates = (
        (REPOSITORY_ROOT / path, BACKEND_ROOT / path)
        if prefer_repository
        else (BACKEND_ROOT / path, REPOSITORY_ROOT / path)
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _create_llm_adapter(settings: Settings) -> LLMAdapter:
    provider = settings.llm_provider.strip().lower()
    if provider == "mock":
        return MockLLM()
    if provider == "deepseek":
        return DeepSeekLLM.from_settings(settings)
    raise LLMConfigurationError(f"不支持的LLM_PROVIDER: {settings.llm_provider}")


@lru_cache
def get_rag_service() -> RAGService:
    """创建并缓存重量级Embedding模型，避免每次HTTP请求重复加载。"""
    settings = get_settings()
    prompt_path = _resolve_path(settings.rag_prompt_path, prefer_repository=True)
    keyword_retriever = KeywordKnowledgeRetriever(
        _resolve_path(settings.rag_knowledge_dir, prefer_repository=True)
    )
    primary_retriever = None
    cache_folder = _resolve_path(settings.embedding_cache_dir)
    if cache_folder.exists() and any(
        path.is_file() and path.name == "config.json"
        for path in cache_folder.rglob("config.json")
    ):
        try:
            primary_retriever = KnowledgeRetriever(
                persist_dir=_resolve_path(settings.rag_vector_store_dir),
                model_name=settings.embedding_model_name,
                device=settings.embedding_device,
                cache_folder=cache_folder,
                collection_name=settings.rag_collection_name,
            )
        except Exception as exc:
            logger.warning(
                "Vector runtime unavailable; keyword retrieval enabled: %s",
                type(exc).__name__,
            )
    else:
        logger.warning("Embedding model cache unavailable; keyword retrieval enabled")

    retriever = ResilientKnowledgeRetriever(primary_retriever, keyword_retriever)
    fallback_llm_service = LLMService(adapter=MockLLM(), prompt_path=prompt_path)
    external_provider = None
    external_model = None
    try:
        adapter = _create_llm_adapter(settings)
        if isinstance(adapter, DeepSeekLLM):
            external_provider = "deepseek"
            external_model = settings.deepseek_model
            llm_service = LLMService(adapter=adapter, prompt_path=prompt_path)
        else:
            llm_service = fallback_llm_service
    except LLMConfigurationError as exc:
        logger.warning("LLM configuration unavailable; preset fallback enabled: %s", exc)
        llm_service = fallback_llm_service
    return RAGService(
        retriever=retriever,
        llm_service=llm_service,
        top_k=settings.rag_top_k,
        min_score=settings.rag_min_score,
        fallback_llm_service=fallback_llm_service,
        external_provider=external_provider,
        external_model=external_model,
    )
