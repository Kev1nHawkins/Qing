"""AI template management permissions, validation, and visibility tests."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.creation import CreationTemplate
from app.models.enums import PublishStatus
from app.models.user import Role, User


def template_payload(*, code: str = "new-poster") -> dict:
    return {
        "name": "新海报模板",
        "code": code,
        "description": "用于模板管理接口测试",
        "prompt_template": "以{culture_element}创作{style}海报。",
        "options_schema": {
            "culture_element": ["木棉", "醒狮"],
            "style": ["国潮", "剪纸"],
        },
        "preview_url": None,
        "status": "DRAFT",
        "culture_item_id": None,
    }


@pytest.fixture
def template_client(tmp_path: Path) -> Iterator[dict]:
    database_path = (tmp_path / "templates.db").resolve().as_posix()
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
                username="template-admin",
                email="template-admin@example.com",
                password_hash="unused",
                nickname="模板管理员",
                role_id=admin_role.id,
            )
            user = User(
                username="template-user",
                email="template-user@example.com",
                password_hash="unused",
                nickname="普通用户",
                role_id=user_role.id,
            )
            session.add_all([admin, user])
            await session.flush()
            templates = [
                CreationTemplate(
                    name="已发布木棉模板",
                    code="published-poster",
                    description="公开模板",
                    prompt_template="生成{subject}海报",
                    options_schema={"subject": ["木棉"]},
                    status=PublishStatus.PUBLISHED.value,
                ),
                CreationTemplate(
                    name="草稿醒狮模板",
                    code="draft-poster",
                    description="内部草稿",
                    prompt_template="生成{subject}海报",
                    options_schema={"subject": ["醒狮"]},
                    status=PublishStatus.DRAFT.value,
                ),
                CreationTemplate(
                    name="下线广彩模板",
                    code="offline-poster",
                    description="历史模板",
                    prompt_template="生成{subject}海报",
                    options_schema={"subject": ["广彩"]},
                    status=PublishStatus.OFFLINE.value,
                ),
            ]
            session.add_all(templates)
            await session.flush()
            state.update(
                {
                    "admin_id": admin.id,
                    "user_id": user.id,
                    "draft_id": templates[1].id,
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


def test_public_list_only_returns_published_templates(template_client: dict) -> None:
    response = template_client["client"].get("/api/v1/creations/templates")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert [item["code"] for item in data["items"]] == ["published-poster"]


def test_admin_list_requires_admin_and_supports_filters(template_client: dict) -> None:
    client = template_client["client"]
    forbidden = client.get(
        "/api/v1/admin/creation-templates",
        headers=template_client["headers"]["user"],
    )
    assert forbidden.status_code == 403

    response = client.get(
        "/api/v1/admin/creation-templates",
        headers=template_client["headers"]["admin"],
        params={"status": "DRAFT", "keyword": "醒狮"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["code"] == "draft-poster"
    assert data["statusCounts"] == {"DRAFT": 1, "PUBLISHED": 1, "OFFLINE": 1}


def test_admin_can_create_and_update_template(template_client: dict) -> None:
    client = template_client["client"]
    headers = template_client["headers"]["admin"]
    created = client.post(
        "/api/v1/creations/templates",
        headers=headers,
        json=template_payload(),
    )
    assert created.status_code == 201
    template_id = created.json()["data"]["id"]

    updated = client.put(
        f"/api/v1/creations/templates/{template_id}",
        headers=headers,
        json={"name": "更新后的模板", "status": "PUBLISHED"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "更新后的模板"
    assert updated.json()["data"]["code"] == "new-poster"
    assert updated.json()["data"]["status"] == "PUBLISHED"


@pytest.mark.parametrize(
    "payload",
    [
        {
            **template_payload(code="missing-option"),
            "prompt_template": "生成{subject}和{unknown}海报",
        },
        {
            **template_payload(code="unused-option"),
            "prompt_template": "生成{culture_element}海报",
        },
        {
            **template_payload(code="empty-values"),
            "options_schema": {"culture_element": []},
            "prompt_template": "生成{culture_element}海报",
        },
    ],
)
def test_invalid_prompt_option_contract_is_rejected(
    template_client: dict,
    payload: dict,
) -> None:
    response = template_client["client"].post(
        "/api/v1/creations/templates",
        headers=template_client["headers"]["admin"],
        json=payload,
    )
    assert response.status_code == 422


def test_duplicate_code_returns_conflict(template_client: dict) -> None:
    response = template_client["client"].post(
        "/api/v1/creations/templates",
        headers=template_client["headers"]["admin"],
        json=template_payload(code="published-poster"),
    )
    assert response.status_code == 409


def test_unpublished_template_cannot_start_creation(template_client: dict) -> None:
    response = template_client["client"].post(
        "/api/v1/creations",
        headers=template_client["headers"]["user"],
        json={
            "template_id": template_client["state"]["draft_id"],
            "title": "不应生成的作品",
            "options": {"subject": "醒狮"},
        },
    )
    assert response.status_code == 409
