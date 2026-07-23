from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin
from app.models.enums import CreationStatus, PublishStatus


class CreationTemplate(Base, IdMixin, TimestampMixin):
    __tablename__ = "creation_templates"

    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(500))
    prompt_template: Mapped[str] = mapped_column(Text)
    options_schema: Mapped[dict | None] = mapped_column(JSON)
    preview_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(20), default=PublishStatus.DRAFT.value, index=True
    )
    culture_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("culture_items.id"), index=True
    )

    creations: Mapped[list["AICreation"]] = relationship(back_populates="template")


class AICreation(Base, IdMixin, TimestampMixin):
    __tablename__ = "ai_creations"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("creation_templates.id"), index=True)
    culture_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("culture_items.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    prompt: Mapped[str] = mapped_column(Text)
    input_payload: Mapped[dict] = mapped_column(JSON)
    output_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default=CreationStatus.PENDING.value, index=True
    )
    error_message: Mapped[str | None] = mapped_column(String(500))
    retry_count: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship(back_populates="creations")
    template: Mapped["CreationTemplate"] = relationship(back_populates="creations")
    culture_item: Mapped["CultureItem | None"] = relationship(back_populates="creations")
    posts: Mapped[list["Post"]] = relationship(back_populates="creation")

