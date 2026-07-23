from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin
from app.models.enums import BadgeRuleType


class PointRecord(Base, IdMixin, TimestampMixin):
    __tablename__ = "point_records"
    __table_args__ = (UniqueConstraint("user_id", "business_key", name="uq_user_point_business"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int]
    balance_after: Mapped[int]
    reason_type: Mapped[str] = mapped_column(String(40), index=True)
    reason_id: Mapped[int | None] = mapped_column(index=True)
    business_key: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="point_records")


class Badge(Base, IdMixin, TimestampMixin):
    __tablename__ = "badges"

    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(500))
    icon_url: Mapped[str | None] = mapped_column(String(500))
    rule_type: Mapped[str] = mapped_column(
        String(40), default=BadgeRuleType.MANUAL.value
    )
    rule_value: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(default=True)

    users: Mapped[list["UserBadge"]] = relationship(back_populates="badge")


class UserBadge(Base, IdMixin, TimestampMixin):
    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id"), index=True)
    awarded_at: Mapped[datetime]
    reason: Mapped[str] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="badges")
    badge: Mapped["Badge"] = relationship(back_populates="users")

