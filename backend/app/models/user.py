from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class Role(Base, IdMixin, TimestampMixin):
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    points_total: Mapped[int] = mapped_column(default=0)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)

    role: Mapped["Role"] = relationship(back_populates="users", lazy="joined")
    task_records: Mapped[list["UserTaskRecord"]] = relationship(back_populates="user")
    creations: Mapped[list["AICreation"]] = relationship(back_populates="user")
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    point_records: Mapped[list["PointRecord"]] = relationship(back_populates="user")
    badges: Mapped[list["UserBadge"]] = relationship(back_populates="user")


class FileAsset(Base, IdMixin, TimestampMixin):
    __tablename__ = "file_assets"

    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    public_url: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(default=0)
    usage_type: Mapped[str | None] = mapped_column(String(50))

