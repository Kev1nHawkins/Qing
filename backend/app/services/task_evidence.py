import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, Request

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
PNG_END = b"\x00\x00\x00\x00IEND\xaeB`\x82"


def upload_root() -> Path:
    configured = os.getenv("LINGCHAO_UPLOAD_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.cwd() / "uploads").resolve()


def _jpeg_dimensions(content: bytes) -> tuple[int, int] | None:
    offset = 2
    while offset + 9 < len(content):
        if content[offset] != 0xFF:
            return None
        marker = content[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(content):
            return None
        segment_length = int.from_bytes(content[offset : offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(content):
            return None
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height = int.from_bytes(content[offset + 3 : offset + 5], "big")
            width = int.from_bytes(content[offset + 5 : offset + 7], "big")
            return width, height
        offset += segment_length
    return None


def _image_dimensions(content: bytes, mime_type: str) -> tuple[int, int] | None:
    if mime_type == "image/png" and len(content) >= 24 and content[12:16] == b"IHDR":
        return (
            int.from_bytes(content[16:20], "big"),
            int.from_bytes(content[20:24], "big"),
        )
    if mime_type == "image/jpeg":
        return _jpeg_dimensions(content)
    if mime_type == "image/webp" and len(content) >= 30:
        chunk_type = content[12:16]
        if chunk_type == b"VP8X":
            width = 1 + int.from_bytes(content[24:27], "little")
            height = 1 + int.from_bytes(content[27:30], "little")
            return width, height
        if chunk_type == b"VP8L" and content[20] == 0x2F:
            bits = content[21:25]
            width = 1 + bits[0] + ((bits[1] & 0x3F) << 8)
            height = 1 + (bits[1] >> 6) + (bits[2] << 2) + ((bits[3] & 0x0F) << 10)
            return width, height
        if chunk_type == b"VP8 " and content[23:26] == b"\x9d\x01\x2a":
            width = int.from_bytes(content[26:28], "little") & 0x3FFF
            height = int.from_bytes(content[28:30], "little") & 0x3FFF
            return width, height
    return None


def validate_image(content: bytes, mime_type: str) -> None:
    valid_signature = False
    if mime_type == "image/jpeg":
        valid_signature = content.startswith(b"\xff\xd8\xff") and content.endswith(b"\xff\xd9")
    elif mime_type == "image/png":
        valid_signature = content.startswith(b"\x89PNG\r\n\x1a\n") and content.endswith(PNG_END)
    elif mime_type == "image/webp":
        valid_signature = (
            len(content) >= 12
            and content.startswith(b"RIFF")
            and content[8:12] == b"WEBP"
            and int.from_bytes(content[4:8], "little") + 8 == len(content)
        )
    if not valid_signature:
        raise HTTPException(status_code=400, detail="图片内容与文件格式不匹配")

    dimensions = _image_dimensions(content, mime_type)
    if not dimensions:
        raise HTTPException(status_code=400, detail="无法解析图片尺寸")
    width, height = dimensions
    if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
        raise HTTPException(status_code=400, detail="图片像素尺寸过大")


async def read_image(request: Request) -> tuple[bytes, str, str]:
    mime_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    suffix = ALLOWED_IMAGE_TYPES.get(mime_type)
    if not suffix:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG 或 WebP 图片")
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="图片大小不能超过 8 MB")
    if not content:
        raise HTTPException(status_code=400, detail="图片内容为空")
    image = bytes(content)
    validate_image(image, mime_type)
    return image, mime_type, suffix


def write_task_evidence(content: bytes, suffix: str) -> tuple[str, Path]:
    relative_key = (Path("task-checkins") / f"{uuid4().hex}{suffix}").as_posix()
    root = upload_root()
    target = (root / relative_key).resolve()
    if root not in target.parents:
        raise HTTPException(status_code=500, detail="上传目录配置无效")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(content)
    return relative_key, target


def resolve_asset_path(storage_key: str) -> Path:
    root = upload_root()
    target = (root / storage_key).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return target


def read_validated_asset(
    storage_key: str,
    expected_size: int,
    mime_type: str,
) -> bytes:
    path = resolve_asset_path(storage_key)
    actual_size = path.stat().st_size
    if actual_size > MAX_IMAGE_BYTES or actual_size != expected_size:
        raise HTTPException(status_code=409, detail="图片凭证完整性校验失败")
    content = path.read_bytes()
    validate_image(content, mime_type)
    return content
