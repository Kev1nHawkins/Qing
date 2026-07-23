from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, DbSession
from app.api.helpers import apply_changes, get_or_404, paginated
from app.core.response import success
from app.models.culture import Location
from app.schemas.culture import LocationCreate, LocationRead, LocationUpdate

router = APIRouter(prefix="/locations", tags=["Location"])


@router.get("", summary="校园地点列表")
async def list_locations(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    culture_item_id: int | None = None,
) -> dict:
    filters = [Location.culture_item_id == culture_item_id] if culture_item_id else []
    return success(
        await paginated(
            db,
            stmt=select(Location).where(*filters).order_by(Location.id),
            count_stmt=select(func.count(Location.id)).where(*filters),
            page=page,
            page_size=page_size,
            schema=LocationRead,
        )
    )


@router.get("/{location_id}", summary="校园地点详情")
async def get_location(location_id: int, db: DbSession) -> dict:
    item = await get_or_404(db, Location, location_id, "校园地点")
    return success(LocationRead.model_validate(item).model_dump())


@router.post("", status_code=201, summary="新增校园地点")
async def create_location(payload: LocationCreate, db: DbSession, _: AdminUser) -> dict:
    item = Location(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return success(LocationRead.model_validate(item).model_dump(), "创建成功")


@router.put("/{location_id}", summary="更新校园地点")
async def update_location(
    location_id: int, payload: LocationUpdate, db: DbSession, _: AdminUser
) -> dict:
    item = await get_or_404(db, Location, location_id, "校园地点")
    apply_changes(item, payload)
    await db.commit()
    await db.refresh(item)
    return success(LocationRead.model_validate(item).model_dump(), "更新成功")


@router.delete("/{location_id}", summary="删除校园地点")
async def delete_location(location_id: int, db: DbSession, _: AdminUser) -> dict:
    item = await get_or_404(db, Location, location_id, "校园地点")
    await db.delete(item)
    await db.commit()
    return success(None, "删除成功")
