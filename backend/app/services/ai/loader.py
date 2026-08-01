"""Markdown 知识库加载器。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    """从一个 Markdown 文件加载得到的知识文档。"""

    text: str
    metadata: dict[str, str]


class MarkdownLoader:
    """递归读取知识目录中的所有 UTF-8 Markdown 文件。"""

    _TITLE_PATTERN = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

    def __init__(self, knowledge_dir: str | Path) -> None:
        self.knowledge_dir = Path(knowledge_dir).resolve()

    def load(self) -> list[KnowledgeDocument]:
        """读取所有 Markdown 文件，并附加稳定、可检索的来源元数据。"""
        if not self.knowledge_dir.is_dir():
            raise FileNotFoundError(f"知识库目录不存在: {self.knowledge_dir}")

        documents: list[KnowledgeDocument] = []
        for path in sorted(self.knowledge_dir.rglob("*.md")):
            if path.name.casefold() == "readme.md":
                continue
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue

            relative_path = path.relative_to(self.knowledge_dir).as_posix()
            title_match = self._TITLE_PATTERN.search(text)
            title = title_match.group(1).strip() if title_match else path.stem
            documents.append(
                KnowledgeDocument(
                    text=text,
                    metadata={
                        "source_id": relative_path,
                        "source_path": relative_path,
                        "file_name": path.name,
                        "title": title,
                    },
                )
            )

        if not documents:
            raise ValueError(f"知识库目录中没有可用的 Markdown 文件: {self.knowledge_dir}")
        return documents
