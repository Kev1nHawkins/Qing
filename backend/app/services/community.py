import json

from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from app.models.community import Post, PostTag
from app.schemas.community import PostRead

MAX_COVER_STORAGE_LENGTH = 500


def decode_post_images(value: str | None) -> list[str]:
    if not value:
        return []
    if not value.startswith("["):
        return [value]
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return [value]
    if not isinstance(parsed, list):
        return [value]
    return [item for item in parsed if isinstance(item, str) and item][:6]


def encode_post_images(values: list[str]) -> str | None:
    images = list(dict.fromkeys(value.strip() for value in values if value.strip()))[:6]
    if not images:
        return None
    encoded = images[0] if len(images) == 1 else json.dumps(
        images,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    if len(encoded) > MAX_COVER_STORAGE_LENGTH:
        raise HTTPException(status_code=400, detail="图片地址总长度过长，请减少图片数量")
    return encoded


def post_load_options() -> tuple:
    return (
        selectinload(Post.author),
        selectinload(Post.culture_item),
        selectinload(Post.creation),
        selectinload(Post.tags).selectinload(PostTag.tag),
    )


def post_payload(post: Post) -> dict:
    image_urls = decode_post_images(post.cover_image_url)
    return PostRead(
        id=post.id,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author_id=post.author_id,
        author_name=post.author.nickname,
        author_avatar_url=post.author.avatar_url,
        culture_item_id=post.culture_item_id,
        culture_item_title=(
            post.culture_item.title if post.culture_item else None
        ),
        creation_id=post.creation_id,
        creation_title=post.creation.title if post.creation else None,
        creation_preview_url=(
            post.creation.output_url if post.creation else None
        ),
        title=post.title,
        content=post.content,
        cover_image_url=image_urls[0] if image_urls else None,
        image_urls=image_urls,
        status=post.status,
        like_count=post.like_count,
        comment_count=post.comment_count,
        favorite_count=post.favorite_count,
        tags=[link.tag.name for link in post.tags],
    ).model_dump()
