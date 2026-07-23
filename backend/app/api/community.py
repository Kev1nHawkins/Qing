from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession
from app.api.helpers import apply_changes, get_or_404, paginated
from app.core.response import success
from app.models.community import Comment, Favorite, Post, PostLike, PostTag, Tag
from app.models.enums import PostStatus
from app.schemas.community import (
    CommentCreate,
    CommentRead,
    PostCreate,
    PostRead,
    PostUpdate,
)

router = APIRouter(prefix="/community", tags=["Community"])


@router.get("/posts", summary="社区帖子列表")
async def list_posts(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    culture_item_id: int | None = None,
) -> dict:
    filters = [Post.status == PostStatus.PUBLISHED.value]
    if culture_item_id:
        filters.append(Post.culture_item_id == culture_item_id)
    return success(
        await paginated(
            db,
            stmt=select(Post).where(*filters).order_by(Post.created_at.desc()),
            count_stmt=select(func.count(Post.id)).where(*filters),
            page=page,
            page_size=page_size,
            schema=PostRead,
        )
    )


@router.get("/posts/{post_id}", summary="社区帖子详情")
async def get_post(post_id: int, db: DbSession) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    return success(PostRead.model_validate(post).model_dump())


@router.post("/posts", status_code=201, summary="发布帖子")
async def create_post(
    payload: PostCreate, db: DbSession, current_user: CurrentUser
) -> dict:
    data = payload.model_dump(exclude={"tags"})
    post = Post(
        **data,
        author_id=current_user.id,
        status=PostStatus.PUBLISHED.value,
    )
    db.add(post)
    await db.flush()
    for name in {tag.strip() for tag in payload.tags if tag.strip()}:
        tag = await db.scalar(select(Tag).where(Tag.name == name))
        if not tag:
            tag = Tag(name=name, slug=name.lower().replace(" ", "-"))
            db.add(tag)
            await db.flush()
        db.add(PostTag(post_id=post.id, tag_id=tag.id))
    await db.commit()
    await db.refresh(post)
    return success(PostRead.model_validate(post).model_dump(), "发布成功")


@router.put("/posts/{post_id}", summary="更新自己的帖子")
async def update_post(
    post_id: int, payload: PostUpdate, db: DbSession, current_user: CurrentUser
) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    if post.author_id != current_user.id and current_user.role.code != "admin":
        raise HTTPException(status_code=403, detail="无权修改该帖子")
    apply_changes(post, payload)
    await db.commit()
    await db.refresh(post)
    return success(PostRead.model_validate(post).model_dump(), "更新成功")


@router.delete("/posts/{post_id}", summary="删除自己的帖子")
async def delete_post(post_id: int, db: DbSession, current_user: CurrentUser) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    if post.author_id != current_user.id and current_user.role.code != "admin":
        raise HTTPException(status_code=403, detail="无权删除该帖子")
    await db.delete(post)
    await db.commit()
    return success(None, "删除成功")


@router.get("/posts/{post_id}/comments", summary="帖子评论列表")
async def list_comments(post_id: int, db: DbSession) -> dict:
    await get_or_404(db, Post, post_id, "帖子")
    comments = (
        await db.scalars(
            select(Comment)
            .where(Comment.post_id == post_id, Comment.is_deleted.is_(False))
            .order_by(Comment.created_at)
        )
    ).all()
    return success([CommentRead.model_validate(item).model_dump() for item in comments])


@router.post("/posts/{post_id}/comments", status_code=201, summary="发表评论")
async def create_comment(
    post_id: int,
    payload: CommentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    comment = Comment(
        post_id=post.id,
        user_id=current_user.id,
        parent_id=payload.parent_id,
        content=payload.content,
    )
    post.comment_count += 1
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return success(CommentRead.model_validate(comment).model_dump(), "评论成功")


@router.post("/posts/{post_id}/like", summary="点赞帖子（幂等）")
async def like_post(post_id: int, db: DbSession, current_user: CurrentUser) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    like = await db.scalar(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id,
        )
    )
    if like:
        return success(
            {"liked": True, "likeCount": post.like_count, "alreadyLiked": True},
            "已点赞，本次未重复计数",
        )
    db.add(PostLike(post_id=post_id, user_id=current_user.id))
    post.like_count += 1
    await db.commit()
    return success(
        {"liked": True, "likeCount": post.like_count, "alreadyLiked": False},
        "点赞成功",
    )


@router.post("/posts/{post_id}/favorite", summary="收藏/取消收藏（幂等）")
async def toggle_favorite(
    post_id: int, db: DbSession, current_user: CurrentUser
) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    favorite = await db.scalar(
        select(Favorite).where(
            Favorite.post_id == post_id,
            Favorite.user_id == current_user.id,
        )
    )
    if favorite:
        await db.delete(favorite)
        post.favorite_count = max(0, post.favorite_count - 1)
        favorited = False
    else:
        db.add(Favorite(post_id=post_id, user_id=current_user.id))
        post.favorite_count += 1
        favorited = True
    await db.commit()
    return success({"favorited": favorited, "favoriteCount": post.favorite_count})
