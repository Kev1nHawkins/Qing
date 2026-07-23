from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, CurrentUser, DbSession
from app.api.helpers import apply_changes, get_or_404, paginated
from app.core.response import success
from app.models.enums import PointReason, TaskStatus, TaskType
from app.models.route import RouteTask, UserTaskRecord
from app.schemas.route import TaskCompleteRequest, TaskCreate, TaskRead, TaskUpdate
from app.services.points import award_points

router = APIRouter(prefix="/tasks", tags=["Task"])


@router.get("", summary="任务节点列表")
async def list_tasks(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    route_id: int | None = None,
) -> dict:
    filters = [RouteTask.route_id == route_id] if route_id else []
    return success(
        await paginated(
            db,
            stmt=select(RouteTask).where(*filters).order_by(RouteTask.route_id, RouteTask.order_no),
            count_stmt=select(func.count(RouteTask.id)).where(*filters),
            page=page,
            page_size=page_size,
            schema=TaskRead,
        )
    )


@router.get("/{task_id}", summary="任务节点详情")
async def get_task(task_id: int, db: DbSession) -> dict:
    task = await get_or_404(db, RouteTask, task_id, "任务节点")
    return success(TaskRead.model_validate(task).model_dump())


@router.post("", status_code=201, summary="新增任务节点")
async def create_task(payload: TaskCreate, db: DbSession, _: AdminUser) -> dict:
    task = RouteTask(**payload.model_dump(mode="json"))
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
    await db.commit()
    await db.refresh(task)
    return success(TaskRead.model_validate(task).model_dump(), "更新成功")


@router.delete("/{task_id}", summary="删除任务节点")
async def delete_task(task_id: int, db: DbSession, _: AdminUser) -> dict:
    task = await get_or_404(db, RouteTask, task_id, "任务节点")
    await db.delete(task)
    await db.commit()
    return success(None, "删除成功")


@router.post("/{task_id}/complete", summary="完成任务（幂等）")
async def complete_task(
    task_id: int,
    payload: TaskCompleteRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    task = await get_or_404(db, RouteTask, task_id, "任务节点")
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

    is_correct = True
    if task.task_type == TaskType.QUIZ.value:
        is_correct = bool(
            payload.answer
            and task.correct_answer
            and payload.answer.strip() == task.correct_answer.strip()
        )
    elif task.task_type == TaskType.QR_CODE.value:
        is_correct = bool(payload.qr_code and payload.qr_code == task.qr_code)
    elif task.task_type == TaskType.SIMULATED_LOCATION.value:
        is_correct = payload.latitude is not None and payload.longitude is not None
    if not is_correct:
        raise HTTPException(status_code=400, detail="任务验证未通过，请检查答案或打卡信息")

    record = existing or UserTaskRecord(user_id=current_user.id, task_id=task_id)
    record.status = TaskStatus.COMPLETED.value
    record.answer = payload.answer
    record.is_correct = True
    record.completed_at = datetime.now(UTC)
    record.awarded_points = task.points
    db.add(record)
    await award_points(
        db,
        user=current_user,
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
            "pointsTotal": current_user.points_total,
            "alreadyCompleted": False,
        },
        "任务完成",
    )

