from pydantic import BaseModel, Field

from app.schemas.common import Timestamped


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=5000)
    culture_item_id: int | None = None
    creation_id: int | None = None
    cover_image_url: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=10)


class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    cover_image_url: str | None = None


class PostRead(Timestamped):
    author_id: int
    author_name: str | None = None
    author_avatar_url: str | None = None
    culture_item_id: int | None
    culture_item_title: str | None = None
    creation_id: int | None
    creation_title: str | None = None
    creation_preview_url: str | None = None
    title: str
    content: str
    cover_image_url: str | None
    status: str
    like_count: int
    comment_count: int
    favorite_count: int
    tags: list[str] = Field(default_factory=list)


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    parent_id: int | None = None


class CommentRead(Timestamped):
    post_id: int
    user_id: int
    author_name: str | None = None
    author_avatar_url: str | None = None
    parent_id: int | None
    content: str
    is_deleted: bool

