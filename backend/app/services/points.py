from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.points import Badge, PointRecord, UserBadge
from app.models.route import UserTaskRecord
from app.models.user import User


async def award_points(
    db: AsyncSession,
    *,
    user: User,
    amount: int,
    reason_type: str,
    reason_id: int | None,
    business_key: str,
    description: str,
) -> PointRecord:
    existing = await db.scalar(
        select(PointRecord).where(
            PointRecord.user_id == user.id,
            PointRecord.business_key == business_key,
        )
    )
    if existing:
        return existing
    user.points_total += amount
    record = PointRecord(
        user_id=user.id,
        amount=amount,
        balance_after=user.points_total,
        reason_type=reason_type,
        reason_id=reason_id,
        business_key=business_key,
        description=description,
    )
    db.add(record)
    await evaluate_badges(db, user)
    return record


async def evaluate_badges(db: AsyncSession, user: User) -> None:
    badges = (await db.scalars(select(Badge).where(Badge.is_active.is_(True)))).all()
    owned = set(
        await db.scalars(select(UserBadge.badge_id).where(UserBadge.user_id == user.id))
    )
    completed_tasks = await db.scalar(
        select(func.count(UserTaskRecord.id)).where(
            UserTaskRecord.user_id == user.id,
            UserTaskRecord.status == "COMPLETED",
        )
    )
    for badge in badges:
        qualifies = (
            badge.rule_type == "POINT_TOTAL"
            and user.points_total >= badge.rule_value
            or badge.rule_type == "TASK_COUNT"
            and (completed_tasks or 0) >= badge.rule_value
        )
        if qualifies and badge.id not in owned:
            db.add(
                UserBadge(
                    user_id=user.id,
                    badge_id=badge.id,
                    awarded_at=datetime.now(UTC),
                    reason=f"满足条件：{badge.rule_type} ≥ {badge.rule_value}",
                )
            )

