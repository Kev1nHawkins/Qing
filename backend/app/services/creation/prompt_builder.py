"""从外部模板构建图片生成 Prompt。"""

from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[3]
HOST_REPOSITORY_ROOT = BACKEND_ROOT.parent
CONTAINER_DATA_DIR = BACKEND_ROOT / "data"
DEFAULT_DATA_DIR = (
    CONTAINER_DATA_DIR if CONTAINER_DATA_DIR.is_dir() else HOST_REPOSITORY_ROOT / "data"
)
DEFAULT_TEMPLATE_PATH = DEFAULT_DATA_DIR / "prompts" / "image_prompt.txt"


class ImagePromptBuilder:
    def __init__(self, template_path: Path = DEFAULT_TEMPLATE_PATH) -> None:
        self.template_path = template_path

    def build(self, culture: str, campus: str, style: str) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        return template.format(culture=culture, campus=campus, style=style)
