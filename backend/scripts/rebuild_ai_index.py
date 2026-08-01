"""离线重建岭南文化Chroma向量索引。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.ai.indexer import IndexBuildError, KnowledgeIndexer  # noqa: E402


def _resolve_input_path(configured_path: str) -> Path:
    path = Path(configured_path)
    if path.is_absolute():
        return path
    for candidate in (REPOSITORY_ROOT / path, BACKEND_ROOT / path):
        if candidate.exists():
            return candidate
    return REPOSITORY_ROOT / path


def _resolve_runtime_path(configured_path: str) -> Path:
    path = Path(configured_path)
    return path if path.is_absolute() else BACKEND_ROOT / path


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="重建岭南文化Markdown知识索引")
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=_resolve_input_path(settings.rag_knowledge_dir),
    )
    parser.add_argument(
        "--persist-dir",
        type=Path,
        default=_resolve_runtime_path(settings.rag_vector_store_dir),
    )
    parser.add_argument("--model", default=settings.embedding_model_name)
    parser.add_argument("--device", default=settings.embedding_device)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=_resolve_runtime_path(settings.embedding_cache_dir),
    )
    parser.add_argument("--collection", default=settings.rag_collection_name)
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = KnowledgeIndexer(
            knowledge_dir=args.knowledge_dir,
            persist_dir=args.persist_dir,
            model_name=args.model,
            device=args.device,
            cache_folder=args.cache_dir,
            collection_name=args.collection,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        ).build()
    except IndexBuildError as exc:
        print(f"AI索引构建失败：{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(
            f"AI索引构建失败：{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"文档数: {result.document_count}")
    print(f"切片数: {result.chunk_count}")
    print(f"向量数: {result.stored_count}")
    print(f"集合名: {result.collection_name}")
    print(f"保存位置: {result.persist_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
