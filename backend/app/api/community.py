from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import case, delete, func, select, update
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DbSession
from app.api.helpers import apply_changes, get_or_404
from app.core.response import success
from app.models.community import Comment, Favorite, Post, PostLike, PostTag, Tag
from app.models.creation import AICreation
from app.models.culture import CultureItem
from app.models.enums import CreationStatus, PostStatus, PublishStatus
from app.models.user import User
from app.schemas.community import (
    CommentCreate,
    CommentRead,
    PostCreate,
    PostUpdate,
)
from app.services.community import post_load_options, post_payload

router = APIRouter(prefix="/community", tags=["Community"])


@router.get("/posts", summary="社区帖子列表")
async def list_posts(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    culture_item_id: int | None = None,
    content_type: str | None = Query(
        None,
        alias="contentType",
        pattern=r"^(AI|CAMPUS|CULTURE)$",
    ),
    tag: str | None = Query(None, max_length=50),
) -> dict:
    filters = [Post.status == PostStatus.PUBLISHED.value]
    if culture_item_id:
        filters.append(Post.culture_item_id == culture_item_id)
    if content_type == "AI":
        filters.append(Post.creation_id.is_not(None))
    elif content_type == "CAMPUS":
        filters.extend(
            [Post.creation_id.is_(None), Post.culture_item_id.is_(None)]
        )
    elif content_type == "CULTURE":
        filters.extend(
            [Post.creation_id.is_(None), Post.culture_item_id.is_not(None)]
        )
    if tag:
        filters.append(Post.tags.any(PostTag.tag.has(Tag.name == tag)))

    total = int(
        (await db.scalar(select(func.count(Post.id)).where(*filters))) or 0
    )
    posts = (
        await db.scalars(
            select(Post)
            .where(*filters)
            .options(*post_load_options())
            .order_by(Post.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return success(
        {
            "total": total,
            "items": [post_payload(post) for post in posts],
            "page": page,
            "pageSize": page_size,
        }
    )


@router.get("/posts/{post_id}", summary="社区帖子详情")
async def get_post(post_id: int, db: DbSession) -> dict:
    post = await db.scalar(
        select(Post)
        .where(
            Post.id == post_id,
            Post.status == PostStatus.PUBLISHED.value,
        )
        .options(*post_load_options())
    )
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return success(post_payload(post))


@router.post("/posts", status_code=201, summary="发布帖子")
async def create_post(
    payload: PostCreate, db: DbSession, current_user: CurrentUser
) -> dict:
    if payload.culture_item_id:
        culture = await db.get(CultureItem, payload.culture_item_id)
        if not culture or culture.status != PublishStatus.PUBLISHED.value:
            raise HTTPException(status_code=404, detail="关联文化条目不存在或未发布")
    if payload.creation_id:
        creation = await db.get(AICreation, payload.creation_id)
        if not creation:
            raise HTTPException(status_code=404, detail="关联 AI 作品不存在")
        if (
            creation.user_id != current_user.id
            and current_user.role.code != "admin"
        ):
            raise HTTPException(status_code=403, detail="只能发布自己的 AI 作品")
        if creation.status != CreationStatus.SUCCESS.value:
            raise HTTPException(status_code=409, detail="AI 作品尚未生成成功")

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
    post = await db.scalar(
        select(Post)
        .where(Post.id == post.id)
        .options(*post_load_options())
    )
    return success(post_payload(post), "发布成功")


@router.put("/posts/{post_id}", summary="更新自己的帖子")
async def update_post(
    post_id: int, payload: PostUpdate, db: DbSession, current_user: CurrentUser
) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    if post.author_id != current_user.id and current_user.role.code != "admin":
        raise HTTPException(status_code=403, detail="无权修改该帖子")
    apply_changes(post, payload)
    await db.commit()
    post = await db.scalar(
        select(Post)
        .where(Post.id == post_id)
        .options(*post_load_options())
    )
    return success(post_payload(post), "更新成功")


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
    post = await get_or_404(db, Post, post_id, "帖子")
    if post.status != PostStatus.PUBLISHED.value:
        raise HTTPException(status_code=404, detail="帖子不存在")
    rows = (
        await db.execute(
            select(Comment, User)
            .join(User, User.id == Comment.user_id)
            .where(Comment.post_id == post_id, Comment.is_deleted.is_(False))
            .order_by(Comment.created_at)
        )
    ).all()
    items = []
    for comment, author in rows:
        item = CommentRead.model_validate(comment).model_dump()
        item.update(
            {
                "author_name": author.nickname,
                "author_avatar_url": author.avatar_url,
            }
        )
        items.append(item)
    return success(items)


@router.post("/posts/{post_id}/comments", status_code=201, summary="发表评论")
async def create_comment(
    post_id: int,
    payload: CommentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    if post.status != PostStatus.PUBLISHED.value:
        raise HTTPException(status_code=409, detail="当前帖子不可评论")
    if payload.parent_id:
        parent = await db.get(Comment, payload.parent_id)
        if (
            not parent
            or parent.post_id != post_id
            or parent.is_deleted
        ):
            raise HTTPException(status_code=422, detail="父评论无效")
    comment = Comment(
        post_id=post.id,
        user_id=current_user.id,
        parent_id=payload.parent_id,
        content=payload.content,
    )
    db.add(comment)
    await db.flush()
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(comment_count=Post.comment_count + 1)
    )
    await db.commit()
    await db.refresh(comment)
    data = CommentRead.model_validate(comment).model_dump()
    data.update(
        {
            "author_name": current_user.nickname,
            "author_avatar_url": current_user.avatar_url,
        }
    )
    return success(data, "评论成功")


@router.post("/posts/{post_id}/like", summary="点赞帖子（幂等）")
async def like_post(post_id: int, db: DbSession, current_user: CurrentUser) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    if post.status != PostStatus.PUBLISHED.value:
        raise HTTPException(status_code=409, detail="当前帖子不可点赞")
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

    inserted = True
    try:
        async with db.begin_nested():
            db.add(PostLike(post_id=post_id, user_id=current_user.id))
            await db.flush()
    except IntegrityError:
        inserted = False

    if inserted:
        await db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(like_count=Post.like_count + 1)
        )
    await db.commit()
    like_count = int(
        (await db.scalar(select(Post.like_count).where(Post.id == post_id))) or 0
    )
    return success(
        {
            "liked": True,
            "likeCount": like_count,
            "alreadyLiked": not inserted,
        },
        "点赞成功" if inserted else "已点赞，本次未重复计数",
    )


@router.post("/posts/{post_id}/favorite", summary="收藏/取消收藏（幂等）")
async def toggle_favorite(
    post_id: int, db: DbSession, current_user: CurrentUser
) -> dict:
    post = await get_or_404(db, Post, post_id, "帖子")
    if post.status != PostStatus.PUBLISHED.value:
        raise HTTPException(status_code=409, detail="当前帖子不可收藏")

    deleted = await db.execute(
        delete(Favorite).where(
            Favorite.post_id == post_id,
            Favorite.user_id == current_user.id,
        )
    )
    if deleted.rowcount:
        await db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(
                favorite_count=case(
                    (Post.favorite_count > 0, Post.favorite_count - 1),
                    else_=0,
                )
            )
        )
        favorited = False
    else:
        inserted = True
        try:
            async with db.begin_nested():
                db.add(Favorite(post_id=post_id, user_id=current_user.id))
                await db.flush()
        except IntegrityError:
            inserted = False
        if inserted:
            await db.execute(
                update(Post)
                .where(Post.id == post_id)
                .values(favorite_count=Post.favorite_count + 1)
            )
        favorited = True
    await db.commit()
    favorite_count = int(
        (await db.scalar(select(Post.favorite_count).where(Post.id == post_id)))
        or 0
    )
    return success(
        {"favorited": favorited, "favoriteCount": favorite_count}
    )
