"""Local knowledge retrieval that remains available without vector dependencies."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any

from app.services.ai.loader import MarkdownLoader
from app.services.ai.splitter import MarkdownTextSplitter


logger = logging.getLogger(__name__)


class KeywordKnowledgeRetriever:
    """Search the checked-in Markdown knowledge base without external models."""

    _NON_WORD = re.compile(r"[^0-9a-zA-Z\u4e00-\u9fff]+")
    _STOP_TERMS = {
        "什么", "为什么", "怎么", "怎样", "是否", "可以", "介绍", "一下",
        "文化", "广州", "相关", "问题", "哪些", "一个", "这个",
    }

    def __init__(self, knowledge_dir: str | Path) -> None:
        documents = MarkdownLoader(knowledge_dir).load()
        self._chunks = MarkdownTextSplitter().split_documents(documents)

    @classmethod
    def _terms(cls, text: str) -> set[str]:
        normalized = cls._NON_WORD.sub("", text).lower()
        terms: set[str] = set()
        for length in (2, 3, 4, 5, 6):
            terms.update(
                normalized[index : index + length]
                for index in range(max(0, len(normalized) - length + 1))
            )
        return {term for term in terms if term not in cls._STOP_TERMS}

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_terms = self._terms(query)
        if not query_terms:
            return []

        ranked: list[tuple[int, Any]] = []
        for chunk in self._chunks:
            searchable = self._NON_WORD.sub(
                "",
                f"{chunk.metadata.get('title', '')}{chunk.metadata.get('section', '')}{chunk.text}",
            ).lower()
            score = sum(1 for term in query_terms if term in searchable)
            if score >= 2:
                ranked.append((score, chunk))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
                "score": min(0.95, 0.60 + score * 0.02),
                "distance": max(0.05, 0.40 - score * 0.02),
            }
            for score, chunk in ranked[:top_k]
        ]


class ResilientKnowledgeRetriever:
    """Use vector search when healthy and cache failures before retrying."""

    def __init__(
        self,
        primary: Any | None,
        fallback: KeywordKnowledgeRetriever,
        retry_cooldown_seconds: float = 300.0,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._retry_cooldown_seconds = retry_cooldown_seconds
        self._primary_failed_until = float("inf") if primary is None else 0.0
        self.last_mode = "keyword"

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        now = time.monotonic()
        if self._primary is not None and now >= self._primary_failed_until:
            try:
                result = self._primary.retrieve(query, top_k=top_k)
                self.last_mode = "vector"
                return result
            except Exception as exc:  # Runtime dependency/network/index failures.
                self._primary_failed_until = now + self._retry_cooldown_seconds
                logger.warning(
                    "Vector retrieval unavailable; using keyword fallback for %.0fs: %s",
                    self._retry_cooldown_seconds,
                    type(exc).__name__,
                )

        self.last_mode = "keyword"
        return self._fallback.retrieve(query, top_k=top_k)
