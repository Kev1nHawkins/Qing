"""RAG索引构建编排与命令入口测试。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.services.ai.indexer import IndexBuildError, KnowledgeIndexer
from app.services.ai.splitter import KnowledgeChunk


class FakeEmbeddingProvider:
    model_name = "fake-embedding"

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.received_texts: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.received_texts = texts
        if self.should_fail:
            raise RuntimeError("模拟Embedding失败")
        return [[float(index), 1.0] for index, _ in enumerate(texts)]


class FakeVectorStore:
    def __init__(self) -> None:
        self.chunks: list[KnowledgeChunk] = []
        self.embeddings: list[list[float]] = []
        self.model_name = ""

    def replace_all(
        self,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
        model_name: str,
    ) -> int:
        self.chunks = chunks
        self.embeddings = embeddings
        self.model_name = model_name
        return len(chunks)


def _write_knowledge(knowledge_dir: Path) -> None:
    knowledge_dir.mkdir()
    (knowledge_dir / "01_test.md").write_text(
        "# 木棉文化\n\n## 广州象征\n\n木棉是广州具有代表性的城市文化符号。",
        encoding="utf-8",
    )
    (knowledge_dir / "README.md").write_text(
        "# 知识库说明\n\n这不是文化知识正文。",
        encoding="utf-8",
    )


def test_indexer_builds_and_reports_counts(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "knowledge"
    _write_knowledge(knowledge_dir)
    embedding = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    result = KnowledgeIndexer(
        knowledge_dir=knowledge_dir,
        persist_dir=tmp_path / "chroma",
        collection_name="lingnan_knowledge",
        embedding_provider=embedding,
        vector_store=vector_store,
    ).build()

    assert result.document_count == 1
    assert result.chunk_count > 0
    assert result.stored_count == result.chunk_count
    assert result.collection_name == "lingnan_knowledge"
    assert len(embedding.received_texts) == result.chunk_count
    assert vector_store.model_name == "fake-embedding"


def test_indexer_reports_missing_knowledge_directory(tmp_path: Path) -> None:
    with pytest.raises(IndexBuildError, match="知识文档加载失败.*知识库目录不存在"):
        KnowledgeIndexer(
            knowledge_dir=tmp_path / "missing",
            persist_dir=tmp_path / "chroma",
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=FakeVectorStore(),
        ).build()


def test_indexer_reports_embedding_failure(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "knowledge"
    _write_knowledge(knowledge_dir)

    with pytest.raises(IndexBuildError, match="向量生成失败.*模拟Embedding失败"):
        KnowledgeIndexer(
            knowledge_dir=knowledge_dir,
            persist_dir=tmp_path / "chroma",
            embedding_provider=FakeEmbeddingProvider(should_fail=True),
            vector_store=FakeVectorStore(),
        ).build()


def test_rebuild_script_reports_clear_failure(tmp_path: Path) -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "rebuild_ai_index.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--knowledge-dir",
            str(tmp_path / "missing"),
            "--persist-dir",
            str(tmp_path / "chroma"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        check=False,
    )

    assert result.returncode == 1
    assert "AI索引构建失败" in result.stderr
    assert "知识库目录不存在" in result.stderr
