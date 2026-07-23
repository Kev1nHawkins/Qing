from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, DbSession
from app.api.helpers import apply_changes, get_or_404, paginated
from app.core.response import success
from app.models.culture import CultureItem
from app.schemas.culture import CultureCreate, CultureRead, CultureUpdate

router = APIRouter(prefix="/cultures", tags=["Culture"])


@router.get("", summary="文化条目列表")
async def list_cultures(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    category: str | None = None,
    keyword: str | None = None,
) -> dict:
    filters = []
    if category:
        filters.append(CultureItem.category == category)
    if keyword:
        filters.append(CultureItem.title.like(f"%{keyword}%"))
    stmt = select(CultureItem).where(*filters).order_by(CultureItem.created_at.desc())
    count_stmt = select(func.count(CultureItem.id)).where(*filters)
    return success(
        await paginated(
            db,
            stmt=stmt,
            count_stmt=count_stmt,
            page=page,
            page_size=page_size,
            schema=CultureRead,
        )
    )


@router.get("/{culture_id}", summary="文化条目详情")
async def get_culture(culture_id: int, db: DbSession) -> dict:
    item = await get_or_404(db, CultureItem, culture_id, "文化条目")
    return success(CultureRead.model_validate(item).model_dump())


@router.post("", status_code=status.HTTP_201_CREATED, summary="新增文化条目")
async def create_culture(payload: CultureCreate, db: DbSession, admin: AdminUser) -> dict:
    item = CultureItem(
        **payload.model_dump(mode="json"),
        created_by_id=admin.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return success(CultureRead.model_validate(item).model_dump(), "创建成功")


@router.put("/{culture_id}", summary="更新文化条目")
async def update_culture(
    culture_id: int, payload: CultureUpdate, db: DbSession, _: AdminUser
) -> dict:
    item = await get_or_404(db, CultureItem, culture_id, "文化条目")
    apply_changes(item, payload)
    await db.commit()
    await db.refresh(item)
    return success(CultureRead.model_validate(item).model_dump(), "更新成功")


@router.delete("/{culture_id}", summary="删除文化条目")
async def delete_culture(
    culture_id: int, db: DbSession, _: AdminUser
) -> dict:
    item = await get_or_404(db, CultureItem, culture_id, "文化条目")
    await db.delete(item)
    await db.commit()
    return success(None, "删除成功")
