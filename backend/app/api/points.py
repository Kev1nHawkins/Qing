from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession
from app.api.helpers import paginated
from app.core.response import success
from app.models.points import PointRecord
from app.schemas.points import PointRead

router = APIRouter(prefix="/points", tags=["Points"])


@router.get("/summary", summary="我的积分概览")
async def point_summary(current_user: CurrentUser) -> dict:
    return success({"pointsTotal": current_user.points_total})


@router.get("/records", summary="我的积分流水")
async def point_records(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict:
    filters = [PointRecord.user_id == current_user.id]
    return success(
        await paginated(
            db,
            stmt=select(PointRecord)
            .where(*filters)
            .order_by(PointRecord.created_at.desc()),
            count_stmt=select(func.count(PointRecord.id)).where(*filters),
            page=page,
            page_size=page_size,
            schema=PointRead,
        )
    )

