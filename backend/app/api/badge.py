from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import AdminUser, CurrentUser, DbSession
from app.core.response import success
from app.models.points import Badge, UserBadge
from app.schemas.points import BadgeCreate, BadgeRead, UserBadgeRead

router = APIRouter(prefix="/badges", tags=["Badge"])


@router.get("", summary="徽章列表")
async def list_badges(db: DbSession) -> dict:
    badges = (
        await db.scalars(select(Badge).where(Badge.is_active.is_(True)).order_by(Badge.id))
    ).all()
    return success([BadgeRead.model_validate(item).model_dump() for item in badges])


@router.get("/mine", summary="我的徽章")
async def my_badges(db: DbSession, current_user: CurrentUser) -> dict:
    badges = (
        await db.scalars(
            select(UserBadge)
            .where(UserBadge.user_id == current_user.id)
            .order_by(UserBadge.awarded_at.desc())
        )
    ).all()
    return success([UserBadgeRead.model_validate(item).model_dump() for item in badges])


@router.post("", status_code=201, summary="新增徽章")
async def create_badge(payload: BadgeCreate, db: DbSession, _: AdminUser) -> dict:
    badge = Badge(**payload.model_dump(mode="json"))
    db.add(badge)
    await db.commit()
    await db.refresh(badge)
    return success(BadgeRead.model_validate(badge).model_dump(), "创建成功")

