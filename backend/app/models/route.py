from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin
from app.models.enums import PublishStatus, TaskStatus, TaskType


class Route(Base, IdMixin, TimestampMixin):
    __tablename__ = "routes"

    title: Mapped[str] = mapped_column(String(120), index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    summary: Mapped[str] = mapped_column(String(500))
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    duration_minutes: Mapped[int] = mapped_column(default=60)
    distance_km: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    status: Mapped[str] = mapped_column(
        String(20), default=PublishStatus.DRAFT.value, index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)

    tasks: Mapped[list["RouteTask"]] = relationship(
        back_populates="route", order_by="RouteTask.order_no", cascade="all, delete-orphan"
    )


class RouteTask(Base, IdMixin, TimestampMixin):
    __tablename__ = "route_tasks"
    __table_args__ = (UniqueConstraint("route_id", "order_no", name="uq_route_task_order"),)

    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), index=True)
    culture_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("culture_items.id"), index=True
    )
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    order_no: Mapped[int] = mapped_column(default=1)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(30), default=TaskType.CHECK_IN.value)
    question: Mapped[str | None] = mapped_column(String(500))
    options: Mapped[list[str] | None] = mapped_column(JSON)
    correct_answer: Mapped[str | None] = mapped_column(String(255))
    points: Mapped[int] = mapped_column(default=10)
    qr_code: Mapped[str | None] = mapped_column(String(120), unique=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    radius_meters: Mapped[int] = mapped_column(default=100)

    route: Mapped["Route"] = relationship(back_populates="tasks")
    culture_item: Mapped["CultureItem | None"] = relationship(back_populates="tasks")
    location: Mapped["Location"] = relationship(back_populates="tasks")
    user_records: Mapped[list["UserTaskRecord"]] = relationship(back_populates="task")


class UserTaskRecord(Base, IdMixin, TimestampMixin):
    __tablename__ = "user_task_records"
    __table_args__ = (UniqueConstraint("user_id", "task_id", name="uq_user_task_record"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("route_tasks.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.IN_PROGRESS.value)
    answer: Mapped[str | None] = mapped_column(String(500))
    is_correct: Mapped[bool | None]
    completed_at: Mapped[datetime | None]
    awarded_points: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship(back_populates="task_records")
    task: Mapped["RouteTask"] = relationship(back_populates="user_records")

