"""从外部模板构建图片生成 Prompt。"""

from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[3]
HOST_REPOSITORY_ROOT = BACKEND_ROOT.parent
CONTAINER_TEMPLATE_PATH = BACKEND_ROOT / "data" / "prompts" / "image_prompt.txt"
HOST_TEMPLATE_PATH = HOST_REPOSITORY_ROOT / "data" / "prompts" / "image_prompt.txt"
DEFAULT_TEMPLATE_PATH = (
    CONTAINER_TEMPLATE_PATH if CONTAINER_TEMPLATE_PATH.is_file() else HOST_TEMPLATE_PATH
)


class ImagePromptBuilder:
    def __init__(self, template_path: Path = DEFAULT_TEMPLATE_PATH) -> None:
        self.template_path = template_path

    def build(self, culture: str, campus: str, style: str) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        return template.format(culture=culture, campus=campus, style=style)
