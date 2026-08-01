"""图片生成器统一接口及 MVP Mock 实现。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from html import escape
from pathlib import Path
from textwrap import wrap


BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "uploads" / "ai-generated"


class ImageGeneratorAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> Path:
        """根据完整 Prompt 生成图片，并返回图片文件路径。"""


class MockImageGenerator(ImageGeneratorAdapter):
    """生成一张可直接预览的 SVG 模拟海报，不调用外部 API。"""

    def __init__(self, task_id: str, output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
        self.task_id = task_id
        self.output_dir = output_dir

    def generate(self, prompt: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{self.task_id}.svg"

        lines = wrap(" ".join(prompt.split()), width=28)[:8]
        prompt_lines = "\n".join(
            f'<text x="80" y="{420 + index * 44}" class="prompt">{escape(line)}</text>'
            for index, line in enumerate(lines)
        )
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
  width="1024" height="1440" viewBox="0 0 1024 1440">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#981f2c"/>
      <stop offset="1" stop-color="#e9b949"/>
    </linearGradient>
  </defs>
  <rect width="1024" height="1440" fill="url(#bg)"/>
  <circle cx="830" cy="210" r="170" fill="#fff4d6" opacity="0.25"/>
  <circle cx="140" cy="1240" r="240" fill="#123c36" opacity="0.32"/>
  <text x="80" y="150" class="eyebrow">LINGCHAO CO-CREATION</text>
  <text x="80" y="260" class="title">岭潮共创</text>
  <text x="80" y="330" class="subtitle">AI 文化海报 · MOCK PREVIEW</text>
  <g>{prompt_lines}</g>
  <text x="80" y="1350" class="footer">比赛 Demo 模拟图片 · 暂未接入真实文生图 API</text>
  <style>
    text {{ font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif; fill: white; }}
    .eyebrow {{ font-size: 27px; letter-spacing: 5px; opacity: .8; }}
    .title {{ font-size: 92px; font-weight: 800; }}
    .subtitle {{ font-size: 34px; font-weight: 600; }}
    .prompt {{ font-size: 27px; opacity: .92; }}
    .footer {{ font-size: 22px; opacity: .72; }}
  </style>
</svg>'''
        output_path.write_text(svg, encoding="utf-8")
        return output_path
