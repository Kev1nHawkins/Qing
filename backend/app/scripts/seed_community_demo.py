import asyncio
import json
import os
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.community import Comment, Favorite, Post, PostLike, PostTag, Tag
from app.models.creation import AICreation, CreationTemplate
from app.models.culture import CultureItem
from app.models.enums import CreationStatus
from app.models.user import Role, User

DEMO_DATA = (
    Path(__file__).resolve().parents[3] / "data" / "demo" / "community-posts.json"
)

TAG_SLUGS = {
    "AI共创": "ai-co-creation",
    "人机共创": "human-ai-co-creation",
    "信息设计": "information-design",
    "公共空间": "public-space",
    "剪纸": "paper-cutting",
    "口述记录": "oral-history",
    "声音档案": "sound-archive",
    "城市观察": "urban-observation",
    "岭南建筑": "lingnan-architecture",
    "岭南文化": "lingnan-culture",
    "广州大学": "guangzhou-university",
    "广彩": "guangcai",
    "影像记录": "visual-record",
    "授权核验": "license-review",
    "文化伦理": "cultural-ethics",
    "文化寻迹": "culture-trail",
    "文化观察": "culture-observation",
    "日常观察": "daily-observation",
    "旧照片": "historical-photo",
    "未来校园": "future-campus",
    "木棉": "kapok",
    "校园打卡": "campus-check-in",
    "校园文化": "campus-culture",
    "校园服务": "campus-service",
    "校园生活": "campus-life",
    "活动回顾": "event-recap",
    "海报设计": "poster-design",
    "粤剧": "cantonese-opera",
    "粤语": "cantonese-language",
    "红棉": "red-kapok",
    "路线公告": "route-notice",
    "角色设计": "character-design",
    "角色设定": "character-concept",
    "视觉设计": "visual-design",
    "设计方法": "design-method",
    "资料核验": "source-review",
    "醒狮文化": "lion-dance",
    "雨天": "rainy-day",
    "青年记忆": "youth-memory",
    "饮食记忆": "food-memory",
    "骑楼": "arcade-building",
    "交互设计": "interaction-design",
    "官方活动": "official-event",
    "审核演示": "moderation-demo",
    "待审核": "pending-review",
    "图书馆": "library",
}

DEMO_USERS = [
    ("lingchao_demo_1", "红棉记录员"),
    ("lingchao_demo_2", "校园寻迹者"),
    ("lingchao_demo_3", "岭潮设计社"),
]


async def ensure_demo_users(session, password: str) -> list[User]:
    role = await session.scalar(select(Role).where(Role.code == "user"))
    if not role:
        raise RuntimeError("请先运行 python -m app.scripts.seed 初始化角色")

    users = []
    for username, nickname in DEMO_USERS:
        user = await session.scalar(select(User).where(User.username == username))
        if not user:
            user = User(
                username=username,
                email=f"{username}@lingchao.example.com",
                password_hash=hash_password(password),
                nickname=nickname,
                role_id=role.id,
                bio="岭潮共创比赛演示账号",
            )
            session.add(user)
            await session.flush()
        else:
            user.nickname = nickname
            user.password_hash = hash_password(password)
        users.append(user)
    return users


async def ensure_tag(session, name: str) -> Tag:
    tag = await session.scalar(select(Tag).where(Tag.name == name))
    if tag:
        return tag
    slug = TAG_SLUGS.get(name)
    if not slug:
        raise RuntimeError(f"演示标签缺少稳定 slug：{name}")
    tag = Tag(name=name, slug=slug)
    session.add(tag)
    await session.flush()
    return tag


async def ensure_ai_creation(
    session,
    *,
    author: User,
    template: CreationTemplate,
    culture: CultureItem,
    spec: dict,
) -> AICreation:
    creation_title = f"演示作品：{spec['title']}"
    creation = await session.scalar(
        select(AICreation).where(
            AICreation.user_id == author.id,
            AICreation.title == creation_title,
        )
    )
    if creation:
        creation.output_url = spec.get("cover_image_url")
        creation.description = spec["content"]
        return creation
    creation = AICreation(
        user_id=author.id,
        template_id=template.id,
        culture_item_id=culture.id,
        title=creation_title,
        prompt="比赛演示作品：基于已核验文化材料进行视觉共创。",
        input_payload={"source": "data/demo/community-posts.json"},
        output_url=spec.get("cover_image_url"),
        description=spec["content"],
        status=CreationStatus.SUCCESS.value,
    )
    session.add(creation)
    await session.flush()
    return creation


async def ensure_interactions(session, posts: list[Post], users: list[User]) -> None:
    for index, post in enumerate(posts):
        if post.status != "PUBLISHED":
            continue
        for user in users[: (index % len(users)) + 1]:
            existing = await session.scalar(
                select(PostLike).where(
                    PostLike.post_id == post.id,
                    PostLike.user_id == user.id,
                )
            )
            if not existing:
                session.add(PostLike(post_id=post.id, user_id=user.id))

        for user in users[: index % 3]:
            existing = await session.scalar(
                select(Favorite).where(
                    Favorite.post_id == post.id,
                    Favorite.user_id == user.id,
                )
            )
            if not existing:
                session.add(Favorite(post_id=post.id, user_id=user.id))

        comment_specs = [
            (users[(index + 1) % len(users)], "这个观察角度很有启发，期待看到下一版。"),
            (users[(index + 2) % len(users)], "已加入我的寻迹清单，也会留意素材来源说明。"),
        ]
        for user, content in comment_specs[: index % 3]:
            existing = await session.scalar(
                select(Comment).where(
                    Comment.post_id == post.id,
                    Comment.user_id == user.id,
                    Comment.content == content,
                )
            )
            if not existing:
                session.add(
                    Comment(
                        post_id=post.id,
                        user_id=user.id,
                        content=content,
                    )
                )
    await session.flush()

    for post in posts:
        post.like_count = int(
            (
                await session.scalar(
                    select(func.count(PostLike.id)).where(
                        PostLike.post_id == post.id
                    )
                )
            )
            or 0
        )
        post.favorite_count = int(
            (
                await session.scalar(
                    select(func.count(Favorite.id)).where(
                        Favorite.post_id == post.id
                    )
                )
            )
            or 0
        )
        post.comment_count = int(
            (
                await session.scalar(
                    select(func.count(Comment.id)).where(
                        Comment.post_id == post.id,
                        Comment.is_deleted.is_(False),
                    )
                )
            )
            or 0
        )


async def main() -> None:
    password = os.getenv("LINGCHAO_DEMO_PASSWORD", "")
    if len(password) < 8:
        raise RuntimeError(
            "请先设置至少 8 位的 LINGCHAO_DEMO_PASSWORD；密码不会写入仓库"
        )
    specs = json.loads(DEMO_DATA.read_text(encoding="utf-8"))
    if len(specs) < 20:
        raise RuntimeError("社区演示内容不得少于 20 条")

    async with AsyncSessionLocal() as session:
        users = await ensure_demo_users(session, password)
        culture = await session.scalar(
            select(CultureItem).where(CultureItem.slug == "kapok-hero-flower")
        )
        template = await session.scalar(
            select(CreationTemplate).where(
                CreationTemplate.code == "kapok-poster"
            )
        )
        if not culture or not template:
            raise RuntimeError("请先运行 python -m app.scripts.seed 初始化文化与模板")

        posts = []
        for index, spec in enumerate(specs):
            author = users[index % len(users)]
            post = await session.scalar(
                select(Post).where(
                    Post.author_id == author.id,
                    Post.title == spec["title"],
                )
            )
            if not post:
                creation = None
                culture_id = None
                if spec["kind"] == "AI":
                    creation = await ensure_ai_creation(
                        session,
                        author=author,
                        template=template,
                        culture=culture,
                        spec=spec,
                    )
                    culture_id = culture.id
                elif spec["kind"] == "CULTURE":
                    culture_id = culture.id

                post = Post(
                    author_id=author.id,
                    culture_item_id=culture_id,
                    creation_id=creation.id if creation else None,
                    title=spec["title"],
                    content=spec["content"],
                    cover_image_url=spec.get("cover_image_url"),
                    status=spec["status"],
                )
                session.add(post)
                await session.flush()
            else:
                post.content = spec["content"]
                post.cover_image_url = spec.get("cover_image_url")
                post.status = spec["status"]
                if spec["kind"] == "AI":
                    creation = await ensure_ai_creation(
                        session,
                        author=author,
                        template=template,
                        culture=culture,
                        spec=spec,
                    )
                    post.creation_id = creation.id
                    post.culture_item_id = culture.id
                elif spec["kind"] == "CULTURE":
                    post.creation_id = None
                    post.culture_item_id = culture.id
                else:
                    post.creation_id = None
                    post.culture_item_id = None

            linked_tag_ids = {
                item.tag_id
                for item in (
                    await session.scalars(
                        select(PostTag).where(PostTag.post_id == post.id)
                    )
                ).all()
            }
            for tag_name in spec["tags"]:
                tag = await ensure_tag(session, tag_name)
                if tag.id not in linked_tag_ids:
                    session.add(PostTag(post_id=post.id, tag_id=tag.id))
                    linked_tag_ids.add(tag.id)
            posts.append(post)

        await ensure_interactions(session, posts, users)
        await session.commit()

    print(
        f"Community demo data is ready: {len(specs)} posts, "
        f"{len(DEMO_USERS)} accounts."
    )


if __name__ == "__main__":
    asyncio.run(main())
