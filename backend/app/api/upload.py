from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.dependencies import CurrentUser, DbSession
from app.core.response import success
from app.models.user import FileAsset

router = APIRouter(prefix="/uploads", tags=["Upload"])

UPLOAD_ROOT = Path("/app/uploads")
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def has_valid_image_signature(content: bytes, mime_type: str) -> bool:
    if mime_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if mime_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if mime_type == "image/webp":
        return (
            len(content) >= 12
            and content.startswith(b"RIFF")
            and content[8:12] == b"WEBP"
        )
    return False


@router.post("/images", status_code=201, summary="上传图片")
async def upload_image(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> dict:
    suffix = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if not suffix:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG 或 WebP 图片")

    content = await file.read(MAX_IMAGE_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="图片内容为空")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="图片大小不能超过 8 MB")
    if not has_valid_image_signature(content, file.content_type or ""):
        raise HTTPException(status_code=400, detail="图片内容与文件格式不匹配")

    relative_path = Path("task-checkins") / f"{uuid4().hex}{suffix}"
    target = UPLOAD_ROOT / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    public_url = f"/uploads/{relative_path.as_posix()}"
    asset = FileAsset(
        owner_id=current_user.id,
        original_name=file.filename or target.name,
        storage_key=relative_path.as_posix(),
        public_url=public_url,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        usage_type="TASK_CHECKIN",
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return success(
        {
            "id": asset.id,
            "url": asset.public_url,
            "mimeType": asset.mime_type,
            "sizeBytes": asset.size_bytes,
        },
        "上传成功",
    )
