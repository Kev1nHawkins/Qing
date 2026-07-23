from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import AdminUser, CurrentUser, DbSession
from app.api.helpers import apply_changes, get_or_404, paginated
from app.core.response import success
from app.models.route import Route, RouteTask, UserTaskRecord
from app.schemas.route import RouteCreate, RouteRead, RouteUpdate, TaskRead

router = APIRouter(prefix="/routes", tags=["Route"])


@router.get("", summary="寻迹路线列表")
async def list_routes(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict:
    return success(
        await paginated(
            db,
            stmt=select(Route).order_by(Route.id),
            count_stmt=select(func.count(Route.id)),
            page=page,
            page_size=page_size,
            schema=RouteRead,
        )
    )


@router.get("/{route_id}", summary="寻迹路线详情及任务")
async def get_route(route_id: int, db: DbSession) -> dict:
    route = await db.scalar(
        select(Route).options(selectinload(Route.tasks)).where(Route.id == route_id)
    )
    if not route:
        return await get_or_404(db, Route, route_id, "寻迹路线")
    data = RouteRead.model_validate(route).model_dump()
    data["tasks"] = [TaskRead.model_validate(task).model_dump() for task in route.tasks]
    return success(data)


@router.post("/{route_id}/start", summary="开始路线（幂等）")
async def start_route(
    route_id: int, db: DbSession, current_user: CurrentUser
) -> dict:
    await get_or_404(db, Route, route_id, "寻迹路线")
    first_task = await db.scalar(
        select(RouteTask)
        .where(RouteTask.route_id == route_id)
        .order_by(RouteTask.order_no)
        .limit(1)
    )
    if not first_task:
        return success({"routeId": route_id, "started": False}, "路线暂无任务")
    record = await db.scalar(
        select(UserTaskRecord).where(
            UserTaskRecord.user_id == current_user.id,
            UserTaskRecord.task_id == first_task.id,
        )
    )
    already_started = record is not None
    if not record:
        record = UserTaskRecord(user_id=current_user.id, task_id=first_task.id)
        db.add(record)
        await db.commit()
        await db.refresh(record)
    return success(
        {
            "routeId": route_id,
            "firstTaskId": first_task.id,
            "recordId": record.id,
            "alreadyStarted": already_started,
        },
        "路线已开始" if not already_started else "路线已在进行中",
    )


@router.post("", status_code=201, summary="新增寻迹路线")
async def create_route(payload: RouteCreate, db: DbSession, admin: AdminUser) -> dict:
    item = Route(**payload.model_dump(mode="json"), created_by_id=admin.id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return success(RouteRead.model_validate(item).model_dump(), "创建成功")


@router.put("/{route_id}", summary="更新寻迹路线")
async def update_route(
    route_id: int, payload: RouteUpdate, db: DbSession, _: AdminUser
) -> dict:
    item = await get_or_404(db, Route, route_id, "寻迹路线")
    apply_changes(item, payload)
    await db.commit()
    await db.refresh(item)
    return success(RouteRead.model_validate(item).model_dump(), "更新成功")


@router.delete("/{route_id}", summary="删除寻迹路线")
async def delete_route(route_id: int, db: DbSession, _: AdminUser) -> dict:
    item = await get_or_404(db, Route, route_id, "寻迹路线")
    await db.delete(item)
    await db.commit()
    return success(None, "删除成功")
