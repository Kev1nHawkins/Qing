import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.base import Base
from app.models.community import Comment, Favorite, Post, PostLike
from app.models.creation import AICreation, CreationTemplate
from app.models.culture import CultureItem
from app.models.enums import CreationStatus, PublishStatus
from app.models.user import Role, User


@pytest.fixture
def community_client(tmp_path: Path) -> Iterator[dict]:
    database_path = (tmp_path / "community.db").resolve().as_posix()
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    state: dict[str, int] = {}

    async def prepare() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            user_role = Role(code="user", name="普通用户")
            admin_role = Role(code="admin", name="管理员")
            session.add_all([user_role, admin_role])
            await session.flush()
            owner = User(
                username="owner",
                email="owner@example.com",
                password_hash=hash_password("Owner123!"),
                nickname="作品作者",
                role_id=user_role.id,
            )
            other = User(
                username="other",
                email="other@example.com",
                password_hash=hash_password("Other123!"),
                nickname="其他用户",
                role_id=user_role.id,
            )
            admin = User(
                username="admin_test",
                email="admin@example.com",
                password_hash=hash_password("Admin123!"),
                nickname="测试管理员",
                role_id=admin_role.id,
            )
            session.add_all([owner, other, admin])
            await session.flush()
            culture = CultureItem(
                title="木棉文化测试条目",
                slug="test-kapok",
                category="岭南文化",
                summary="测试摘要",
                content="测试正文",
                source_title="测试来源",
                status=PublishStatus.PUBLISHED.value,
                created_by_id=admin.id,
            )
            session.add(culture)
            await session.flush()
            template = CreationTemplate(
                name="测试海报",
                code="test-poster",
                description="测试模板",
                prompt_template="{subject}",
                options_schema={"subject": ["木棉"]},
                status=PublishStatus.PUBLISHED.value,
                culture_item_id=culture.id,
            )
            session.add(template)
            await session.flush()
            owner_creation = AICreation(
                user_id=owner.id,
                template_id=template.id,
                culture_item_id=culture.id,
                title="作者的 AI 作品",
                prompt="木棉",
                input_payload={"subject": "木棉"},
                output_url="https://example.com/owner.webp",
                status=CreationStatus.SUCCESS.value,
            )
            other_creation = AICreation(
                user_id=other.id,
                template_id=template.id,
                culture_item_id=culture.id,
                title="其他用户的 AI 作品",
                prompt="木棉",
                input_payload={"subject": "木棉"},
                output_url="https://example.com/other.webp",
                status=CreationStatus.SUCCESS.value,
            )
            session.add_all([owner_creation, other_creation])
            await session.flush()
            state.update(
                {
                    "owner_id": owner.id,
                    "other_id": other.id,
                    "admin_id": admin.id,
                    "culture_id": culture.id,
                    "owner_creation_id": owner_creation.id,
                    "other_creation_id": other_creation.id,
                }
            )
            await session.commit()

    asyncio.run(prepare())

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    headers = {
        "owner": {
            "Authorization": (
                "Bearer "
                + create_access_token(str(state["owner_id"]), role="user")
            )
        },
        "other": {
            "Authorization": (
                "Bearer "
                + create_access_token(str(state["other_id"]), role="user")
            )
        },
        "admin": {
            "Authorization": (
                "Bearer "
                + create_access_token(str(state["admin_id"]), role="admin")
            )
        },
    }
    with TestClient(app) as client:
        yield {
            "client": client,
            "state": state,
            "headers": headers,
            "session_factory": session_factory,
        }
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def create_post(context: dict, **overrides) -> dict:
    payload = {
        "title": "红棉寻迹测试作品",
        "content": "用于社区接口自动化测试。",
        "culture_item_id": context["state"]["culture_id"],
        "tags": ["木棉", "测试"],
    }
    payload.update(overrides)
    response = context["client"].post(
        "/api/v1/community/posts",
        headers=context["headers"]["owner"],
        json=payload,
    )
    assert response.status_code == 201
    assert response.json()["requestId"]
    return response.json()["data"]


def test_like_is_idempotent_and_count_matches_relation(community_client: dict) -> None:
    post = create_post(community_client)
    path = f"/api/v1/community/posts/{post['id']}/like"

    first = community_client["client"].post(
        path,
        headers=community_client["headers"]["owner"],
    )
    second = community_client["client"].post(
        path,
        headers=community_client["headers"]["owner"],
    )

    assert first.status_code == 200
    assert first.json()["data"] == {
        "liked": True,
        "likeCount": 1,
        "alreadyLiked": False,
    }
    assert second.status_code == 200
    assert second.json()["data"] == {
        "liked": True,
        "likeCount": 1,
        "alreadyLiked": True,
    }

    async def verify() -> None:
        async with community_client["session_factory"]() as session:
            relation_count = await session.scalar(
                select(func.count(PostLike.id)).where(
                    PostLike.post_id == post["id"]
                )
            )
            stored_count = await session.scalar(
                select(Post.like_count).where(Post.id == post["id"])
            )
            assert relation_count == stored_count == 1

    asyncio.run(verify())


def test_comment_and_favorite_counts_match_relations(community_client: dict) -> None:
    post = create_post(community_client)
    client = community_client["client"]
    headers = community_client["headers"]["owner"]

    comment = client.post(
        f"/api/v1/community/posts/{post['id']}/comments",
        headers=headers,
        json={"content": "第一条测试评论", "parent_id": None},
    )
    assert comment.status_code == 201
    assert comment.json()["data"]["author_name"] == "作品作者"

    favorite_on = client.post(
        f"/api/v1/community/posts/{post['id']}/favorite",
        headers=headers,
    )
    favorite_off = client.post(
        f"/api/v1/community/posts/{post['id']}/favorite",
        headers=headers,
    )
    assert favorite_on.json()["data"] == {
        "favorited": True,
        "favoriteCount": 1,
    }
    assert favorite_off.json()["data"] == {
        "favorited": False,
        "favoriteCount": 0,
    }

    async def verify() -> None:
        async with community_client["session_factory"]() as session:
            comment_relations = await session.scalar(
                select(func.count(Comment.id)).where(
                    Comment.post_id == post["id"],
                    Comment.is_deleted.is_(False),
                )
            )
            favorite_relations = await session.scalar(
                select(func.count(Favorite.id)).where(
                    Favorite.post_id == post["id"]
                )
            )
            stored = await session.get(Post, post["id"])
            assert stored
            assert stored.comment_count == comment_relations == 1
            assert stored.favorite_count == favorite_relations == 0

    asyncio.run(verify())


def test_author_admin_and_normal_user_permissions(community_client: dict) -> None:
    post = create_post(community_client)
    client = community_client["client"]

    forbidden_update = client.put(
        f"/api/v1/community/posts/{post['id']}",
        headers=community_client["headers"]["other"],
        json={"title": "越权修改"},
    )
    forbidden_admin = client.get(
        "/api/v1/admin/posts",
        headers=community_client["headers"]["owner"],
    )
    assert forbidden_update.status_code == 403
    assert forbidden_admin.status_code == 403

    author_update = client.put(
        f"/api/v1/community/posts/{post['id']}",
        headers=community_client["headers"]["owner"],
        json={"title": "作者更新后的标题"},
    )
    assert author_update.status_code == 200
    assert author_update.json()["data"]["title"] == "作者更新后的标题"
    assert author_update.json()["data"]["author_name"] == "作品作者"
    assert set(author_update.json()["data"]["tags"]) == {"木棉", "测试"}

    admin_list = client.get(
        "/api/v1/admin/posts",
        headers=community_client["headers"]["admin"],
    )
    assert admin_list.status_code == 200
    assert admin_list.json()["data"]["total"] == 1
    assert admin_list.json()["data"]["items"][0]["author_name"] == "作品作者"

    offline = client.patch(
        f"/api/v1/admin/posts/{post['id']}/review",
        headers=community_client["headers"]["admin"],
        json={"status": "OFFLINE"},
    )
    assert offline.status_code == 200
    assert offline.json()["data"]["status"] == "OFFLINE"
    assert client.get(
        f"/api/v1/community/posts/{post['id']}"
    ).status_code == 404


def test_only_creation_owner_or_admin_can_publish_ai_work(
    community_client: dict,
) -> None:
    forbidden = community_client["client"].post(
        "/api/v1/community/posts",
        headers=community_client["headers"]["owner"],
        json={
            "title": "越权关联作品",
            "content": "不应创建成功",
            "creation_id": community_client["state"]["other_creation_id"],
            "tags": [],
        },
    )
    assert forbidden.status_code == 403

    created = create_post(
        community_client,
        title="作者自己的 AI 作品",
        creation_id=community_client["state"]["owner_creation_id"],
    )
    assert created["creation_title"] == "作者的 AI 作品"
    assert created["creation_preview_url"] == "https://example.com/owner.webp"
