"""知识库加载、切片、向量化和Chroma持久化编排。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.services.ai.embedding_provider import LocalEmbeddingProvider
from app.services.ai.loader import MarkdownLoader
from app.services.ai.splitter import KnowledgeChunk, MarkdownTextSplitter
from app.services.ai.vector_store import ChromaVectorStore


class EmbeddingProvider(Protocol):
    model_name: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    def replace_all(
        self,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
        model_name: str,
    ) -> int: ...


class IndexBuildError(RuntimeError):
    """RAG索引构建失败，错误消息会标明失败阶段。"""


@dataclass(frozen=True, slots=True)
class IndexBuildResult:
    document_count: int
    chunk_count: int
    stored_count: int
    collection_name: str
    persist_dir: Path


class KnowledgeIndexer:
    """可重复执行地重建岭南文化知识索引。"""

    def __init__(
        self,
        knowledge_dir: str | Path,
        persist_dir: str | Path,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cpu",
        cache_folder: str | Path | None = None,
        collection_name: str = "lingnan_knowledge",
        chunk_size: int = 700,
        chunk_overlap: int = 100,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.knowledge_dir = Path(knowledge_dir).resolve()
        self.persist_dir = Path(persist_dir).resolve()
        self.model_name = model_name
        self.device = device
        self.cache_folder = Path(cache_folder).resolve() if cache_folder else None
        self.collection_name = collection_name
        self.loader = MarkdownLoader(self.knowledge_dir)
        self.splitter = MarkdownTextSplitter(chunk_size, chunk_overlap)
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def build(self) -> IndexBuildResult:
        documents = self._load_documents()
        chunks = self._split_documents(documents)
        embedding_provider = self.embedding_provider or LocalEmbeddingProvider(
            model_name=self.model_name,
            device=self.device,
            cache_folder=self.cache_folder,
        )
        embeddings = self._embed_chunks(embedding_provider, chunks)
        vector_store = self.vector_store or ChromaVectorStore(
            persist_dir=self.persist_dir,
            collection_name=self.collection_name,
        )
        stored_count = self._store_chunks(
            vector_store,
            chunks,
            embeddings,
            embedding_provider.model_name,
        )
        return IndexBuildResult(
            document_count=len(documents),
            chunk_count=len(chunks),
            stored_count=stored_count,
            collection_name=self.collection_name,
            persist_dir=self.persist_dir,
        )

    def _load_documents(self) -> list:
        try:
            return self.loader.load()
        except (OSError, ValueError) as exc:
            raise IndexBuildError(f"知识文档加载失败：{exc}") from exc

    def _split_documents(self, documents: list) -> list[KnowledgeChunk]:
        try:
            chunks = self.splitter.split_documents(documents)
        except (TypeError, ValueError) as exc:
            raise IndexBuildError(f"知识切片失败：{exc}") from exc
        if not chunks:
            raise IndexBuildError("知识切片失败：没有生成可用的知识片段")
        return chunks

    @staticmethod
    def _embed_chunks(
        embedding_provider: EmbeddingProvider,
        chunks: list[KnowledgeChunk],
    ) -> list[list[float]]:
        try:
            embeddings = embedding_provider.embed_documents(
                [chunk.text for chunk in chunks]
            )
        except Exception as exc:
            raise IndexBuildError(
                f"向量生成失败：{type(exc).__name__}: {exc}"
            ) from exc
        if len(embeddings) != len(chunks):
            raise IndexBuildError(
                f"向量生成失败：知识片段数为{len(chunks)}，"
                f"但向量数为{len(embeddings)}"
            )
        return embeddings

    @staticmethod
    def _store_chunks(
        vector_store: VectorStore,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
        model_name: str,
    ) -> int:
        try:
            return vector_store.replace_all(chunks, embeddings, model_name)
        except Exception as exc:
            raise IndexBuildError(
                f"Chroma索引保存失败：{type(exc).__name__}: {exc}"
            ) from exc
