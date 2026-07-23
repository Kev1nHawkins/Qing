from uuid import uuid4

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.dependencies import AdminUser, DbSession
from app.api.helpers import get_or_404, paginated
from app.core.response import success
from app.models.community import Post
from app.models.creation import AICreation
from app.models.culture import CultureItem
from app.models.enums import PointReason
from app.models.points import PointRecord
from app.models.route import UserTaskRecord
from app.models.user import User
from app.schemas.auth import UserRead
from app.schemas.points import AdminPointAdjust, AdminPostReview
from app.services.points import award_points

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", summary="管理看板")
async def dashboard(db: DbSession, _: AdminUser) -> dict:
    users, cultures, creations, posts, completed_tasks = [
        int(value or 0)
        for value in [
            await db.scalar(select(func.count(User.id))),
            await db.scalar(select(func.count(CultureItem.id))),
            await db.scalar(select(func.count(AICreation.id))),
            await db.scalar(select(func.count(Post.id))),
            await db.scalar(
                select(func.count(UserTaskRecord.id)).where(
                    UserTaskRecord.status == "COMPLETED"
                )
            ),
        ]
    ]
    return success(
        {
            "userCount": users,
            "cultureCount": cultures,
            "creationCount": creations,
            "postCount": posts,
            "completedTaskCount": completed_tasks,
        }
    )


@router.get("/users", summary="用户管理列表")
async def list_users(
    db: DbSession,
    _: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict:
    return success(
        await paginated(
            db,
            stmt=select(User).order_by(User.created_at.desc()),
            count_stmt=select(func.count(User.id)),
            page=page,
            page_size=page_size,
            schema=UserRead,
        )
    )


@router.patch("/posts/{post_id}/review", summary="审核或下架帖子")
async def review_post(
    post_id: int, payload: AdminPostReview, db: DbSession, _: AdminUser
) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    post.status = payload.status
    await db.commit()
    return success({"postId": post.id, "status": post.status}, "审核状态已更新")


@router.post("/users/{user_id}/points", summary="人工调整用户积分")
async def adjust_points(
    user_id: int,
    payload: AdminPointAdjust,
    db: DbSession,
    _: AdminUser,
) -> dict:
    user = await get_or_404(db, User, user_id, "用户")
    record = await award_points(
        db,
        user=user,
        amount=payload.amount,
        reason_type=PointReason.ADMIN_ADJUST.value,
        reason_id=None,
        business_key=f"admin-adjust:{uuid4()}",
        description=payload.description,
    )
    await db.commit()
    await db.refresh(record)
    return success(
        {
            "recordId": record.id,
            "amount": record.amount,
            "pointsTotal": user.points_total,
        },
        "积分调整成功",
    )

