"""面向 Markdown 知识文件的标题感知文本切片。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.services.ai.loader import KnowledgeDocument


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    """待向量化的知识片段。"""

    chunk_id: str
    text: str
    metadata: dict[str, str | int]


class MarkdownTextSplitter:
    """优先按 Markdown 标题和段落切分，并为长段落添加重叠窗口。"""

    _HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 100) -> None:
        if chunk_size < 100:
            raise ValueError("chunk_size不能小于100")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap必须大于等于0且小于chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: list[KnowledgeDocument]) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for document in documents:
            chunks.extend(self._split_document(document))
        return chunks

    def _split_document(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        sections = self._markdown_sections(document.text)
        result: list[KnowledgeChunk] = []

        for section_title, section_text in sections:
            for piece in self._split_long_text(section_text):
                clean_piece = piece.strip()
                if not clean_piece:
                    continue
                chunk_index = len(result)
                source_id = document.metadata["source_id"]
                digest = hashlib.sha256(
                    f"{source_id}\n{chunk_index}\n{clean_piece}".encode()
                ).hexdigest()[:24]
                metadata: dict[str, str | int] = {
                    **document.metadata,
                    "section": section_title,
                    "chunk_index": chunk_index,
                }
                result.append(
                    KnowledgeChunk(chunk_id=digest, text=clean_piece, metadata=metadata)
                )
        return result

    def _markdown_sections(self, text: str) -> list[tuple[str, str]]:
        sections: list[tuple[str, str]] = []
        heading_stack: list[str] = []
        buffer: list[str] = []

        def flush() -> None:
            content = "\n".join(buffer).strip()
            if content:
                title = " > ".join(heading_stack) if heading_stack else "文档信息"
                sections.append((title, content))
            buffer.clear()

        for line in text.splitlines():
            match = self._HEADING_PATTERN.match(line)
            if match:
                flush()
                level = len(match.group(1))
                heading_stack[level - 1 :] = [match.group(2).strip()]
                buffer.append(line)
            else:
                buffer.append(line)
        flush()
        return sections

    def _split_long_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
        pieces: list[str] = []
        current = ""
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                pieces.append(current)
            if len(paragraph) <= self.chunk_size:
                current = paragraph
            else:
                pieces.extend(self._sliding_windows(paragraph))
                current = ""
        if current:
            pieces.append(current)
        return pieces

    def _sliding_windows(self, text: str) -> list[str]:
        step = self.chunk_size - self.chunk_overlap
        return [text[start : start + self.chunk_size] for start in range(0, len(text), step)]
