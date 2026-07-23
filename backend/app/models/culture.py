from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin
from app.models.enums import PublishStatus


class CultureItem(Base, IdMixin, TimestampMixin):
    __tablename__ = "culture_items"

    title: Mapped[str] = mapped_column(String(120), index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    summary: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    source_title: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(20), default=PublishStatus.DRAFT.value, index=True
    )
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)

    locations: Mapped[list["Location"]] = relationship(back_populates="culture_item")
    tasks: Mapped[list["RouteTask"]] = relationship(back_populates="culture_item")
    creations: Mapped[list["AICreation"]] = relationship(back_populates="culture_item")
    posts: Mapped[list["Post"]] = relationship(back_populates="culture_item")


class Location(Base, IdMixin, TimestampMixin):
    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(String(120), index=True)
    address: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    image_url: Mapped[str | None] = mapped_column(String(500))
    culture_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("culture_items.id"), index=True
    )

    culture_item: Mapped["CultureItem | None"] = relationship(back_populates="locations")
    tasks: Mapped[list["RouteTask"]] = relationship(back_populates="location")

