from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin
from app.models.enums import PostStatus


class Post(Base, IdMixin, TimestampMixin):
    __tablename__ = "posts"

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    culture_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("culture_items.id"), index=True
    )
    creation_id: Mapped[int | None] = mapped_column(ForeignKey("ai_creations.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(20), default=PostStatus.PENDING.value, index=True
    )
    like_count: Mapped[int] = mapped_column(default=0)
    comment_count: Mapped[int] = mapped_column(default=0)
    favorite_count: Mapped[int] = mapped_column(default=0)

    author: Mapped["User"] = relationship(back_populates="posts")
    culture_item: Mapped["CultureItem | None"] = relationship(back_populates="posts")
    creation: Mapped["AICreation | None"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    tags: Mapped[list["PostTag"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class Comment(Base, IdMixin, TimestampMixin):
    __tablename__ = "comments"

    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id"), index=True)
    content: Mapped[str] = mapped_column(String(1000))
    is_deleted: Mapped[bool] = mapped_column(default=False)

    post: Mapped["Post"] = relationship(back_populates="comments")


class PostLike(Base, IdMixin, TimestampMixin):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_user_like"),)

    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    post: Mapped["Post"] = relationship(back_populates="likes")


class Favorite(Base, IdMixin, TimestampMixin):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_user_favorite"),)

    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    post: Mapped["Post"] = relationship(back_populates="favorites")


class Tag(Base, IdMixin, TimestampMixin):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    posts: Mapped[list["PostTag"]] = relationship(back_populates="tag")


class PostTag(Base, IdMixin, TimestampMixin):
    __tablename__ = "post_tags"
    __table_args__ = (UniqueConstraint("post_id", "tag_id", name="uq_post_tag"),)

    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), index=True)

    post: Mapped["Post"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="posts")

