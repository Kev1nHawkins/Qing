"""Admin read endpoints and public publication-boundary tests."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.culture import CultureItem, Location
from app.models.route import Route, RouteTask
from app.models.user import Role, User


@pytest.fixture
def admin_read_client(tmp_path: Path) -> Iterator[dict]:
    database_path = (tmp_path / "admin-read.db").resolve().as_posix()
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
            admin_role = Role(code="admin", name="管理员")
            user_role = Role(code="user", name="普通用户")
            session.add_all([admin_role, user_role])
            await session.flush()
            admin = User(
                username="boundary-admin",
                email="boundary-admin@example.com",
                password_hash="unused",
                nickname="边界管理员",
                role_id=admin_role.id,
            )
            user = User(
                username="boundary-user",
                email="boundary-user@example.com",
                password_hash="unused",
                nickname="普通用户",
                role_id=user_role.id,
            )
            session.add_all([admin, user])
            await session.flush()
            published_culture = CultureItem(
                title="已发布文化",
                slug="published-culture",
                category="岭南文化",
                summary="公开摘要",
                content="公开内容",
                source_title="测试来源",
                status="PUBLISHED",
                created_by_id=admin.id,
            )
            draft_culture = CultureItem(
                title="草稿文化",
                slug="draft-culture",
                category="岭南文化",
                summary="内部摘要",
                content="内部内容",
                source_title="内部来源",
                status="DRAFT",
                created_by_id=admin.id,
            )
            session.add_all([published_culture, draft_culture])
            await session.flush()
            location = Location(
                name="测试地点",
                address="测试地址",
                latitude=Decimal("23.0000000"),
                longitude=Decimal("113.0000000"),
                culture_item_id=published_culture.id,
            )
            session.add(location)
            await session.flush()
            published_route = Route(
                title="已发布路线",
                slug="published-route",
                summary="公开路线",
                duration_minutes=30,
                distance_km=Decimal("1.00"),
                status="PUBLISHED",
                created_by_id=admin.id,
            )
            draft_route = Route(
                title="草稿路线",
                slug="draft-route",
                summary="内部路线",
                duration_minutes=45,
                distance_km=Decimal("2.00"),
                status="DRAFT",
                created_by_id=admin.id,
            )
            session.add_all([published_route, draft_route])
            await session.flush()
            session.add(
                RouteTask(
                    route_id=draft_route.id,
                    culture_item_id=draft_culture.id,
                    location_id=location.id,
                    order_no=1,
                    title="内部任务",
                    description="管理员可见任务",
                    task_type="CHECK_IN",
                    points=10,
                )
            )
            await session.commit()
            state.update(
                {
                    "admin_id": admin.id,
                    "user_id": user.id,
                    "draft_culture_id": draft_culture.id,
                }
            )

    asyncio.run(prepare())

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    headers = {
        "admin": {
            "Authorization": "Bearer "
            + create_access_token(str(state["admin_id"]), role="admin")
        },
        "user": {
            "Authorization": "Bearer "
            + create_access_token(str(state["user_id"]), role="user")
        },
    }
    with TestClient(app) as client:
        yield {"client": client, "headers": headers, "state": state}
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


@pytest.mark.parametrize(
    "path",
    ["/admin/cultures", "/admin/routes", "/admin/locations"],
)
def test_admin_reads_require_admin(admin_read_client: dict, path: str) -> None:
    client = admin_read_client["client"]
    assert client.get(f"/api/v1{path}").status_code == 401
    assert client.get(
        f"/api/v1{path}", headers=admin_read_client["headers"]["user"]
    ).status_code == 403
    assert client.get(
        f"/api/v1{path}", headers=admin_read_client["headers"]["admin"]
    ).status_code == 200


def test_public_cultures_hide_unpublished_items(admin_read_client: dict) -> None:
    client = admin_read_client["client"]
    response = client.get("/api/v1/cultures", params={"pageSize": 100})
    assert response.status_code == 200
    assert [item["slug"] for item in response.json()["data"]["items"]] == [
        "published-culture"
    ]
    assert client.get(
        f"/api/v1/cultures/{admin_read_client['state']['draft_culture_id']}"
    ).status_code == 404


def test_admin_reads_include_drafts_and_route_tasks(admin_read_client: dict) -> None:
    client = admin_read_client["client"]
    headers = admin_read_client["headers"]["admin"]
    cultures = client.get(
        "/api/v1/admin/cultures", headers=headers, params={"pageSize": 100}
    ).json()["data"]
    assert cultures["total"] == 2
    assert {item["status"] for item in cultures["items"]} == {"DRAFT", "PUBLISHED"}

    routes = client.get(
        "/api/v1/admin/routes", headers=headers, params={"pageSize": 100}
    ).json()["data"]
    assert routes["total"] == 2
    draft = next(item for item in routes["items"] if item["slug"] == "draft-route")
    assert [task["title"] for task in draft["tasks"]] == ["内部任务"]
