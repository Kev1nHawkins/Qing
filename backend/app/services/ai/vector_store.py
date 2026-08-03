"""Chroma 持久化向量库封装。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.ai.splitter import KnowledgeChunk


class ChromaVectorStore:
    """管理岭南文化知识片段的 Chroma 集合。"""

    def __init__(
        self,
        persist_dir: str | Path,
        collection_name: str = "lingnan_knowledge",
    ) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "缺少chromadb，请先执行: pip install -r requirements.txt"
            ) from exc

        self.persist_dir = Path(persist_dir).resolve()
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))

    def replace_all(
        self,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
        model_name: str,
    ) -> int:
        """在向量生成成功后整体替换集合，避免重复索引。"""
        if not chunks:
            raise ValueError("没有可写入的知识片段")
        if len(chunks) != len(embeddings):
            raise ValueError("知识片段数量与向量数量不一致")

        existing_names = {collection.name for collection in self._client.list_collections()}
        if self.collection_name in existing_names:
            self._client.delete_collection(self.collection_name)

        collection = self._client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine", "embedding_model": model_name},
        )
        batch_size = 100
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            collection.add(
                ids=[chunk.chunk_id for chunk in batch],
                documents=[chunk.text for chunk in batch],
                metadatas=[chunk.metadata for chunk in batch],
                embeddings=embeddings[start : start + batch_size],
            )
        return collection.count()

    def query(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """按余弦距离返回最相关的知识片段。"""
        if top_k < 1:
            raise ValueError("top_k必须大于0")
        collection = self._client.get_collection(self.collection_name)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents") or [[]]
        metadatas = result.get("metadatas") or [[]]
        distances = result.get("distances") or [[]]
        ids = result.get("ids") or [[]]
        return [
            {
                "chunk_id": chunk_id,
                "text": document,
                "metadata": metadata or {},
                "distance": distance,
                "score": 1.0 - distance,
            }
            for chunk_id, document, metadata, distance in zip(
                ids[0], documents[0], metadatas[0], distances[0], strict=True
            )
        ]
