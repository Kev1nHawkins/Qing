import hmac
from datetime import UTC, datetime
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query, Request, Response
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, CurrentUser, DbSession
from app.api.helpers import apply_changes, get_or_404, paginated
from app.core.response import success
from app.models.enums import PointReason, TaskStatus, TaskType
from app.models.route import Route, RouteTask, UserTaskRecord
from app.models.user import FileAsset, User
from app.schemas.route import TaskCompleteRequest, TaskCreate, TaskRead, TaskUpdate
from app.services.points import award_points
from app.services.task_evidence import (
    read_image,
    read_validated_asset,
    write_task_evidence,
)

router = APIRouter(prefix="/tasks", tags=["Task"])


def validate_task_configuration(task: RouteTask) -> None:
    if task.task_type == TaskType.QUIZ.value and not task.correct_answer:
        raise HTTPException(status_code=422, detail="问答任务必须配置正确答案")
    if task.task_type == TaskType.QR_CODE.value and not task.qr_code:
        raise HTTPException(status_code=422, detail="二维码任务必须配置校验内容")
    if task.task_type == TaskType.SIMULATED_LOCATION.value and (
        task.latitude is None or task.longitude is None
    ):
        raise HTTPException(status_code=422, detail="位置任务必须配置经纬度")


def distance_meters(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    earth_radius_meters = 6_371_000
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(latitude_a))
        * cos(radians(latitude_b))
        * sin(longitude_delta / 2) ** 2
    )
    return 2 * earth_radius_meters * asin(sqrt(haversine))


async def get_completable_task(db: DbSession, task_id: int) -> RouteTask:
    task = await db.scalar(
        select(RouteTask)
        .join(Route, Route.id == RouteTask.route_id)
        .where(RouteTask.id == task_id, Route.status == "PUBLISHED")
    )
    if not task:
        raise HTTPException(status_code=404, detail="任务节点不存在或所属路线未发布")
    return task


async def require_started_route(db: DbSession, user_id: int, route_id: int) -> None:
    first_task_id = await db.scalar(
        select(RouteTask.id)
        .where(RouteTask.route_id == route_id)
        .order_by(RouteTask.order_no, RouteTask.id)
        .limit(1)
    )
    started = (
        await db.scalar(
            select(UserTaskRecord.id).where(
                UserTaskRecord.user_id == user_id,
                UserTaskRecord.task_id == first_task_id,
            )
        )
        if first_task_id
        else None
    )
    if not started:
        raise HTTPException(status_code=409, detail="请先领取路线再完成任务")


@router.get("", summary="任务节点列表")
async def list_tasks(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    route_id: int | None = None,
) -> dict:
    filters = [RouteTask.route_id == route_id] if route_id is not None else []
    return success(
        await paginated(
            db,
            stmt=select(RouteTask)
            .join(Route, Route.id == RouteTask.route_id)
            .where(Route.status == "PUBLISHED", *filters)
            .order_by(RouteTask.route_id, RouteTask.order_no),
            count_stmt=select(func.count(RouteTask.id))
            .join(Route, Route.id == RouteTask.route_id)
            .where(Route.status == "PUBLISHED", *filters),
            page=page,
            page_size=page_size,
            schema=TaskRead,
        )
    )


@router.get("/{task_id}", summary="任务节点详情")
async def get_task(task_id: int, db: DbSession) -> dict:
    task = await get_completable_task(db, task_id)
    return success(TaskRead.model_validate(task).model_dump())


@router.post("", status_code=201, summary="新增任务节点")
async def create_task(payload: TaskCreate, db: DbSession, _: AdminUser) -> dict:
    task = RouteTask(**payload.model_dump(mode="json"))
    validate_task_configuration(task)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return success(TaskRead.model_validate(task).model_dump(), "创建成功")


@router.put("/{task_id}", summary="更新任务节点")
async def update_task(
    task_id: int, payload: TaskUpdate, db: DbSession, _: AdminUser
) -> dict:
    task = await get_or_404(db, RouteTask, task_id, "任务节点")
    apply_changes(task, payload)
    validate_task_configuration(task)
    await db.commit()
    await db.refresh(task)
    return success(TaskRead.model_validate(task).model_dump(), "更新成功")


@router.delete("/{task_id}", summary="删除任务节点")
async def delete_task(task_id: int, db: DbSession, _: AdminUser) -> dict:
    task = await get_or_404(db, RouteTask, task_id, "任务节点")
    await db.delete(task)
    await db.commit()
    return success(None, "删除成功")


@router.post("/{task_id}/evidence", status_code=201, summary="上传图片打卡凭证")
async def upload_task_evidence(
    task_id: int,
    db: DbSession,
    current_user: CurrentUser,
    request: Request,
) -> dict:
    task = await get_completable_task(db, task_id)
    if task.task_type != TaskType.CHECK_IN.value:
        raise HTTPException(status_code=409, detail="当前任务不接受图片凭证")
    locked_user = await db.scalar(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    if not locked_user:
        raise HTTPException(status_code=401, detail="用户不存在")
    await require_started_route(db, current_user.id, task.route_id)
    completed = await db.scalar(
        select(UserTaskRecord.id).where(
            UserTaskRecord.user_id == current_user.id,
            UserTaskRecord.task_id == task_id,
            UserTaskRecord.status == TaskStatus.COMPLETED.value,
        )
    )
    if completed:
        raise HTTPException(status_code=409, detail="任务已完成，无需重复上传图片")
    evidence_count = await db.scalar(
        select(func.count(FileAsset.id)).where(
            FileAsset.owner_id == current_user.id,
            FileAsset.usage_type == f"TASK_CHECKIN:{task_id}",
        )
    )
    if (evidence_count or 0) >= 5:
        raise HTTPException(status_code=429, detail="该任务上传次数过多，请使用已有图片凭证")

    content, mime_type, suffix = await read_image(request)
    storage_key, target = write_task_evidence(content, suffix)
    submitted_name = unquote(request.headers.get("x-file-name", "")[:1024]).replace(
        "\\", "/"
    )
    original_name = "".join(
        character for character in submitted_name.rsplit("/", 1)[-1] if character.isprintable()
    ).strip()[:255] or target.name
    asset = FileAsset(
        owner_id=current_user.id,
        original_name=original_name,
        storage_key=storage_key,
        public_url=f"/api/v1/tasks/{task_id}/evidence/pending",
        mime_type=mime_type,
        size_bytes=len(content),
        usage_type=f"TASK_CHECKIN:{task_id}",
    )
    db.add(asset)
    try:
        await db.flush()
        asset.public_url = f"/api/v1/tasks/{task_id}/evidence/{asset.id}"
        await db.commit()
    except Exception:
        target.unlink(missing_ok=True)
        raise
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


@router.get("/{task_id}/evidence/{asset_id}", summary="读取我的图片打卡凭证")
async def get_task_evidence(
    task_id: int,
    asset_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    asset = await db.scalar(
        select(FileAsset).where(
            FileAsset.id == asset_id,
            FileAsset.owner_id == current_user.id,
            FileAsset.usage_type == f"TASK_CHECKIN:{task_id}",
        )
    )
    if not asset:
        raise HTTPException(status_code=404, detail="图片凭证不存在")
    content = read_validated_asset(
        asset.storage_key,
        asset.size_bytes,
        asset.mime_type,
    )
    return Response(
        content=content,
        media_type=asset.mime_type,
        headers={
            "Cache-Control": "private, max-age=300",
            "Content-Disposition": f'inline; filename="{asset.id}{Path(asset.storage_key).suffix}"',
            "Cross-Origin-Resource-Policy": "same-origin",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/{task_id}/complete", summary="完成任务（幂等）")
async def complete_task(
    task_id: int,
    payload: TaskCompleteRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    task = await get_completable_task(db, task_id)
    locked_user = await db.scalar(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    if not locked_user:
        raise HTTPException(status_code=401, detail="用户不存在")
    await require_started_route(db, current_user.id, task.route_id)
    existing = await db.scalar(
        select(UserTaskRecord).where(
            UserTaskRecord.user_id == current_user.id,
            UserTaskRecord.task_id == task_id,
        )
    )
    if existing and existing.status == TaskStatus.COMPLETED.value:
        return success(
            {
                "recordId": existing.id,
                "awardedPoints": existing.awarded_points,
                "alreadyCompleted": True,
            },
            "任务已完成，本次未重复加分",
        )

    record_answer: str | None = None
    distance: float | None = None
    is_verified = False
    answer_is_correct: bool | None = None
    if task.task_type == TaskType.QUIZ.value:
        record_answer = payload.answer.strip() if payload.answer else None
        is_verified = bool(record_answer)
        answer_is_correct = bool(
            payload.answer
            and task.correct_answer
            and payload.answer.strip() == task.correct_answer.strip()
        )
    elif task.task_type == TaskType.CHECK_IN.value:
        asset = (
            await db.scalar(
                select(FileAsset).where(
                    FileAsset.id == payload.file_asset_id,
                    FileAsset.owner_id == current_user.id,
                    FileAsset.usage_type == f"TASK_CHECKIN:{task_id}",
                )
            )
            if payload.file_asset_id
            else None
        )
        if asset:
            read_validated_asset(
                asset.storage_key,
                asset.size_bytes,
                asset.mime_type,
            )
        is_verified = asset is not None
        answer_is_correct = is_verified
        record_answer = f"ASSET:{asset.id}" if asset else None
    elif task.task_type == TaskType.QR_CODE.value:
        is_verified = bool(
            payload.qr_code
            and task.qr_code
            and hmac.compare_digest(payload.qr_code, task.qr_code)
        )
        answer_is_correct = is_verified
    elif task.task_type == TaskType.SIMULATED_LOCATION.value:
        if (
            payload.latitude is not None
            and payload.longitude is not None
            and task.latitude is not None
            and task.longitude is not None
        ):
            distance = distance_meters(
                float(payload.latitude),
                float(payload.longitude),
                float(task.latitude),
                float(task.longitude),
            )
            is_verified = distance <= task.radius_meters
            answer_is_correct = is_verified
    if not is_verified:
        raise HTTPException(status_code=400, detail="任务验证未通过，请检查答案或打卡凭证")

    record = existing or UserTaskRecord(user_id=current_user.id, task_id=task_id)
    record.status = TaskStatus.COMPLETED.value
    record.answer = record_answer
    record.is_correct = answer_is_correct
    record.completed_at = datetime.now(UTC)
    record.awarded_points = task.points
    db.add(record)
    await award_points(
        db,
        user=locked_user,
        amount=task.points,
        reason_type=PointReason.TASK_COMPLETE.value,
        reason_id=task.id,
        business_key=f"task:{task.id}",
        description=f"完成任务：{task.title}",
    )
    await db.commit()
    await db.refresh(record)
    return success(
        {
            "recordId": record.id,
            "awardedPoints": task.points,
            "pointsTotal": locked_user.points_total,
            "alreadyCompleted": False,
            "distanceMeters": round(distance, 2) if distance is not None else None,
        },
        "任务完成",
    )
