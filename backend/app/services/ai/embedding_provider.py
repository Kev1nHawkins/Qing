"""本地文本 Embedding 服务封装。"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


class LocalEmbeddingProvider:
    """使用 Sentence Transformers 生成归一化中文文本向量。"""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cpu",
        cache_folder: str | Path | None = None,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "缺少sentence-transformers，请先执行: pip install -r requirements.txt"
            ) from exc

        self.model_name = model_name
        self._model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=str(cache_folder) if cache_folder is not None else None,
        )

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """批量生成文档向量。"""
        if not texts:
            return []
        vectors = self._model.encode(
            list(texts),
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        """生成查询向量。"""
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("查询文本不能为空")
        vector = self._model.encode(clean_text, normalize_embeddings=True)
        return vector.tolist()
