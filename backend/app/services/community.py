from sqlalchemy.orm import selectinload

from app.models.community import Post, PostTag
from app.schemas.community import PostRead


def post_load_options() -> tuple:
    return (
        selectinload(Post.author),
        selectinload(Post.culture_item),
        selectinload(Post.creation),
        selectinload(Post.tags).selectinload(PostTag.tag),
    )


def post_payload(post: Post) -> dict:
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
        cover_image_url=post.cover_image_url,
        status=post.status,
        like_count=post.like_count,
        comment_count=post.comment_count,
        favorite_count=post.favorite_count,
        tags=[link.tag.name for link in post.tags],
    ).model_dump()
