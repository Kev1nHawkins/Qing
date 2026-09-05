from uuid import uuid4

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select

from app.api.dependencies import AdminUser, DbSession
from app.api.helpers import get_or_404, paginated
from app.core.response import success
from app.models.community import Post
from app.models.creation import AICreation, CreationTemplate
from app.models.culture import CultureItem
from app.models.enums import PointReason, PostStatus, PublishStatus
from app.models.points import PointRecord
from app.models.route import UserTaskRecord
from app.models.user import User
from app.schemas.auth import UserRead
from app.schemas.creation import TemplateRead
from app.schemas.points import AdminPointAdjust, AdminPostReview
from app.services.community import post_load_options, post_payload
from app.services.points import award_points

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/creation-templates", summary="AI 创作模板管理列表")
async def list_creation_templates(
    db: DbSession,
    _: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    status: PublishStatus | None = None,
    keyword: str | None = Query(None, max_length=120),
) -> dict:
    filters = []
    if status:
        filters.append(CreationTemplate.status == status.value)
    if keyword and keyword.strip():
        normalized = f"%{keyword.strip()}%"
        filters.append(
            or_(
                CreationTemplate.name.ilike(normalized),
                CreationTemplate.code.ilike(normalized),
                CreationTemplate.description.ilike(normalized),
            )
        )

    total = int(
        (await db.scalar(select(func.count(CreationTemplate.id)).where(*filters))) or 0
    )
    templates = (
        await db.scalars(
            select(CreationTemplate)
            .where(*filters)
            .order_by(CreationTemplate.updated_at.desc(), CreationTemplate.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    grouped = (
        await db.execute(
            select(CreationTemplate.status, func.count(CreationTemplate.id)).group_by(
                CreationTemplate.status
            )
        )
    ).all()
    status_counts = {item.value: 0 for item in PublishStatus}
    status_counts.update({item_status: int(count) for item_status, count in grouped})
    return success(
        {
            "total": total,
            "items": [
                TemplateRead.model_validate(template).model_dump()
                for template in templates
            ],
            "page": page,
            "pageSize": page_size,
            "statusCounts": status_counts,
        }
    )


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


@router.get("/posts", summary="社区帖子审核列表")
async def list_posts(
    db: DbSession,
    _: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    status: str | None = Query(
        None,
        pattern=r"^(PENDING|PUBLISHED|REJECTED|OFFLINE)$",
    ),
    keyword: str | None = Query(None, max_length=120),
) -> dict:
    filters = []
    if status:
        filters.append(Post.status == status)
    if keyword:
        normalized = f"%{keyword.strip()}%"
        filters.append(
            or_(
                Post.title.ilike(normalized),
                Post.content.ilike(normalized),
                User.nickname.ilike(normalized),
                User.username.ilike(normalized),
            )
        )

    base = select(Post).join(User, User.id == Post.author_id).where(*filters)
    count_stmt = (
        select(func.count(Post.id))
        .select_from(Post)
        .join(User, User.id == Post.author_id)
        .where(*filters)
    )
    total = int((await db.scalar(count_stmt)) or 0)
    posts = (
        await db.scalars(
            base.options(*post_load_options())
            .order_by(Post.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    grouped = (
        await db.execute(
            select(Post.status, func.count(Post.id)).group_by(Post.status)
        )
    ).all()
    status_counts = {item.value: 0 for item in PostStatus}
    status_counts.update({item_status: int(count) for item_status, count in grouped})
    return success(
        {
            "total": total,
            "items": [post_payload(post) for post in posts],
            "page": page,
            "pageSize": page_size,
            "statusCounts": status_counts,
        }
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

