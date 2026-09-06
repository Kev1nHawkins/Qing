"""Image generator contract and an explicitly labelled local template provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from hashlib import sha256
from html import escape
from pathlib import Path
from textwrap import wrap


BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "uploads" / "ai-generated"


class ImageGeneratorAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> Path:
        """Generate an image file and return its local path."""


class MockImageGenerator(ImageGeneratorAdapter):
    """Render a varied local SVG; this never calls an external image model."""

    PALETTES = (
        ("#9b2634", "#e8b44f", "#173f35", "#fff3d5"),
        ("#1e6654", "#dceadf", "#d99b36", "#f7f3e8"),
        ("#8c2130", "#f1d5ad", "#402a54", "#fff7e7"),
        ("#174d68", "#de694e", "#f3d47a", "#f5f0e5"),
    )

    def __init__(
        self,
        task_id: str,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
        size: str = "768x1344",
    ) -> None:
        self.task_id = task_id
        self.output_dir = output_dir
        self.size = size

    def generate(self, prompt: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{self.task_id}.svg"
        digest = sha256(f"{self.task_id}|{prompt}".encode("utf-8")).hexdigest()
        variant = int(digest[:4], 16) % len(self.PALETTES)
        primary, secondary, accent, paper = self.PALETTES[variant]
        rotation = 10 + int(digest[4:6], 16) % 28
        offset = 110 + int(digest[6:8], 16) % 170

        lines = wrap(" ".join(prompt.split()), width=24)[:7]
        prompt_lines = "\n".join(
            f'<text x="72" y="{510 + index * 48}" class="prompt">{escape(line)}</text>'
            for index, line in enumerate(lines)
        )
        variant_art = (
            f'<path d="M0 980 Q310 {720 + offset} 620 980 T1024 920 V1440 H0Z" fill="{secondary}" opacity=".36"/>'
            if variant % 2 == 0
            else f'<g transform="rotate({rotation} 512 720)" opacity=".24"><rect x="-180" y="330" width="1380" height="170" fill="{accent}"/><rect x="-180" y="650" width="1380" height="90" fill="{paper}"/></g>'
        )
        if "图书馆" in prompt:
            campus_art = f'''<g transform="translate(590 760)" opacity=".72">
  <path d="M0 120 L170 0 L340 120Z" fill="{paper}"/>
  <rect y="120" width="340" height="220" fill="{paper}"/>
  <g fill="{primary}"><rect x="35" y="160" width="48" height="130"/><rect x="110" y="160" width="48" height="130"/><rect x="185" y="160" width="48" height="130"/><rect x="260" y="160" width="48" height="130"/></g>
</g>'''
        elif "红棉广场" in prompt:
            campus_art = f'''<g transform="translate(700 860)" opacity=".76" fill="{paper}">
  <circle cx="0" cy="-90" r="54"/><circle cx="70" cy="-20" r="54"/><circle cx="0" cy="50" r="54"/><circle cx="-70" cy="-20" r="54"/><circle cx="0" cy="-20" r="34" fill="{accent}"/>
  <path d="M-220 170 H220 L160 235 H-160Z"/>
</g>'''
        else:
            campus_art = f'<path d="M610 1110 L790 780 L970 1110Z" fill="{paper}" opacity=".58"/>'

        if "剪纸" in prompt:
            style_art = f'<path d="M35 420 L260 350 L220 570 L430 500" fill="none" stroke="{paper}" stroke-width="16" stroke-dasharray="18 12" opacity=".6"/>'
        elif "现代插画" in prompt:
            style_art = f'<g opacity=".42"><rect x="40" y="390" width="220" height="35" fill="{accent}"/><rect x="115" y="445" width="300" height="22" fill="{paper}"/></g>'
        else:
            style_art = f'<circle cx="180" cy="440" r="95" fill="none" stroke="{accent}" stroke-width="18" opacity=".46"/>'
        try:
            width, height = (int(value) for value in self.size.split("x", 1))
        except (TypeError, ValueError):
            width, height = 768, 1344
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 1024 1440">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{primary}"/>
      <stop offset="1" stop-color="{secondary}"/>
    </linearGradient>
    <pattern id="grain" width="42" height="42" patternUnits="userSpaceOnUse">
      <circle cx="7" cy="9" r="2" fill="{paper}" opacity=".18"/>
      <path d="M20 0 L42 22 M0 20 L22 42" stroke="{paper}" opacity=".09"/>
    </pattern>
  </defs>
  <rect width="1024" height="1440" fill="url(#bg)"/>
  <rect width="1024" height="1440" fill="url(#grain)"/>
  {variant_art}
  {campus_art}
  {style_art}
  <circle cx="{760 + variant * 35}" cy="210" r="{125 + variant * 18}" fill="{paper}" opacity=".22"/>
  <rect x="45" y="45" width="934" height="1350" rx="{8 + variant * 7}" fill="none" stroke="{paper}" opacity=".55"/>
  <text x="72" y="135" class="eyebrow">LINGCHAO · LOCAL TEMPLATE V{variant + 1}</text>
  <text x="72" y="260" class="title">岭潮共创</text>
  <text x="72" y="335" class="subtitle">演示降级模板 · 非 AI 生图</text>
  <line x1="72" y1="390" x2="620" y2="390" stroke="{accent}" stroke-width="8"/>
  <g>{prompt_lines}</g>
  <text x="72" y="1340" class="footer">MOCK_TEMPLATE / variant {variant + 1} / {escape(self.task_id)}</text>
  <style>
    text {{ font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif; fill: white; }}
    .eyebrow {{ font-size: 24px; letter-spacing: 4px; opacity: .82; }}
    .title {{ font-size: 92px; font-weight: 800; }}
    .subtitle {{ font-size: 32px; font-weight: 700; fill: {paper}; }}
    .prompt {{ font-size: 29px; opacity: .94; }}
    .footer {{ font-size: 20px; opacity: .75; }}
  </style>
</svg>'''
        output_path.write_text(svg, encoding="utf-8")
        return output_path
