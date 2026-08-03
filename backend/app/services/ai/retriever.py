"""知识库向量检索器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.ai.embedding_provider import LocalEmbeddingProvider
from app.services.ai.vector_store import ChromaVectorStore


class KnowledgeRetriever:
    """使用与建库相同的 Embedding 模型查询 Chroma。"""

    def __init__(
        self,
        persist_dir: str | Path,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cpu",
        cache_folder: str | Path | None = None,
        collection_name: str = "lingnan_knowledge",
    ) -> None:
        self.embedding_provider = LocalEmbeddingProvider(
            model_name=model_name,
            device=device,
            cache_folder=cache_folder,
        )
        self.vector_store = ChromaVectorStore(
            persist_dir,
            collection_name=collection_name,
        )

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_embedding = self.embedding_provider.embed_query(query)
        return self.vector_store.query(query_embedding, top_k=top_k)
