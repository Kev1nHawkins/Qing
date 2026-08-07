import asyncio
import json
from collections import Counter
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.models.base import Base
from app.models.community import Comment, Favorite, Post, PostLike, PostTag
from app.models.creation import AICreation, CreationTemplate
from app.models.culture import CultureItem, Location
from app.models.route import RouteTask
from app.models.user import Role, User
from app.scripts import seed_community_demo
from app.scripts.seed import CULTURE_SPECS, ensure_demo_routes


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMUNITY_DEMO_DATA = REPO_ROOT / "data" / "demo" / "community-posts.json"


def test_culture_demo_specs_are_complete_and_unique() -> None:
    assert len(CULTURE_SPECS) == 30

    slugs = [spec["slug"] for spec in CULTURE_SPECS]
    assert len(slugs) == len(set(slugs))
    assert "kapok-hero-flower" in slugs

    required_fields = {
        "title",
        "slug",
        "category",
        "summary",
        "content",
        "cover_image_url",
        "source_title",
        "source_url",
        "status",
    }
    for spec in CULTURE_SPECS:
        assert set(spec) == required_fields
        assert spec["title"].strip()
        assert spec["category"].strip()
        assert 50 <= len(spec["summary"].strip()) <= 120
        assert len(spec["content"].strip()) >= 400
        assert len(spec["content"].split("\n\n")) == 5
        assert spec["cover_image_url"].startswith("/demo/culture-covers/")
        assert spec["source_title"].strip()
        assert spec["source_url"].startswith("https://")
        assert spec["status"] == "PUBLISHED"
        for frontend in ("frontend-user", "frontend-admin"):
            cover_path = (
                REPO_ROOT / frontend / "public" / spec["cover_image_url"].lstrip("/")
            )
            assert cover_path.is_file()


def test_community_demo_preserves_existing_kind_semantics() -> None:
    specs = json.loads(COMMUNITY_DEMO_DATA.read_text(encoding="utf-8"))
    culture_slugs = {spec["slug"] for spec in CULTURE_SPECS}
    culture_covers = {spec["cover_image_url"] for spec in CULTURE_SPECS}

    assert len(specs) == 40
    assert Counter(spec["status"] for spec in specs) == {
        "PUBLISHED": 30,
        "PENDING": 4,
        "REJECTED": 2,
        "OFFLINE": 4,
    }
    assert Counter(
        spec["kind"] for spec in specs if spec["status"] == "PUBLISHED"
    ) == {"AI": 12, "CAMPUS": 10, "CULTURE": 8}

    for spec in specs:
        assert spec["cover_image_url"] in culture_covers
        if spec["kind"] == "CAMPUS":
            assert spec["culture_slug"] is None
        else:
            assert spec["culture_slug"] in culture_slugs


def test_demo_seed_scripts_are_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = (tmp_path / "demo-content.db").resolve().as_posix()
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    monkeypatch.setattr(seed_community_demo, "AsyncSessionLocal", session_factory)
    monkeypatch.setenv("LINGCHAO_DEMO_PASSWORD", "DemoOnly123!")

    async def snapshot() -> tuple[int, ...]:
        async with session_factory() as session:
            return (
                int(await session.scalar(select(func.count(CultureItem.id))) or 0),
                int(await session.scalar(select(func.count(Post.id))) or 0),
                int(await session.scalar(select(func.count(AICreation.id))) or 0),
                int(await session.scalar(select(func.count(PostTag.id))) or 0),
                int(await session.scalar(select(func.count(PostLike.id))) or 0),
                int(await session.scalar(select(func.count(Favorite.id))) or 0),
                int(await session.scalar(select(func.count(Comment.id))) or 0),
            )

    async def exercise() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            user_role = Role(code="user", name="普通用户")
            admin_role = Role(code="admin", name="管理员")
            session.add_all([user_role, admin_role])
            await session.flush()
            admin = User(
                username="content_admin",
                email="content-admin@example.com",
                password_hash="not-used-in-seed-test",
                nickname="内容管理员",
                role_id=admin_role.id,
            )
            session.add(admin)
            await session.flush()

            await ensure_demo_routes(session, admin)
            await session.commit()
            await ensure_demo_routes(session, admin)
            await session.commit()

        await seed_community_demo.main()
        first_snapshot = await snapshot()
        await seed_community_demo.main()
        second_snapshot = await snapshot()

        assert first_snapshot == second_snapshot
        assert first_snapshot[:3] == (30, 40, 18)

        async with session_factory() as session:
            cultures = (await session.scalars(select(CultureItem))).all()
            culture_ids_by_slug = {item.slug: item.id for item in cultures}
            assert len(culture_ids_by_slug) == 30
            kapok_id = culture_ids_by_slug["kapok-hero-flower"]

            route_culture_ids = set(
                await session.scalars(select(RouteTask.culture_item_id).distinct())
            )
            location_culture_ids = set(
                await session.scalars(select(Location.culture_item_id).distinct())
            )
            template = await session.scalar(
                select(CreationTemplate).where(
                    CreationTemplate.code == "kapok-poster"
                )
            )
            assert route_culture_ids == {kapok_id}
            assert location_culture_ids == {kapok_id}
            assert template is not None
            assert template.culture_item_id == kapok_id

            post_specs = {
                spec["title"]: spec
                for spec in json.loads(
                    COMMUNITY_DEMO_DATA.read_text(encoding="utf-8")
                )
            }
            posts = (await session.scalars(select(Post))).all()
            public_kinds: Counter[str] = Counter()
            for post in posts:
                spec = post_specs[post.title]
                if spec["kind"] == "AI":
                    assert post.creation_id is not None
                    assert post.culture_item_id == culture_ids_by_slug[
                        spec["culture_slug"]
                    ]
                elif spec["kind"] == "CULTURE":
                    assert post.creation_id is None
                    assert post.culture_item_id == culture_ids_by_slug[
                        spec["culture_slug"]
                    ]
                else:
                    assert post.creation_id is None
                    assert post.culture_item_id is None
                if post.status == "PUBLISHED":
                    public_kinds[spec["kind"]] += 1

            assert public_kinds == {"AI": 12, "CAMPUS": 10, "CULTURE": 8}

        await engine.dispose()

    asyncio.run(exercise())
