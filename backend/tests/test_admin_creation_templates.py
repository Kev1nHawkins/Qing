"""AI template management permissions, validation, and visibility tests."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.creation import CreationTemplate
from app.models.enums import PublishStatus
from app.models.user import Role, User
from app.scripts.seed import ensure_creation_templates
from app.services.creation.task_runner import get_creation_task_runner
from app.services.creation.system_templates import SYSTEM_FREE_IMAGE_TEMPLATE_CODE


class NoopCreationTaskRunner:
    def __init__(self) -> None:
        self.submitted: list[int] = []

    def submit(self, creation_id: int) -> None:
        self.submitted.append(creation_id)


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
def template_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict]:
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "image_generator_provider", "mock")
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
                    "published_id": templates[0].id,
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

    runner = NoopCreationTaskRunner()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_creation_task_runner] = lambda: runner
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
        yield {
            "client": client,
            "headers": headers,
            "state": state,
            "runner": runner,
            "session_factory": session_factory,
        }
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


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"subject": "木棉", "unknown": "额外值"},
        {"subject": "不在候选范围内"},
        {"subject": 123},
    ],
)
def test_creation_options_must_match_template_schema(
    template_client: dict,
    options: dict,
) -> None:
    response = template_client["client"].post(
        "/api/v1/creations",
        headers=template_client["headers"]["user"],
        json={
            "template_id": template_client["state"]["published_id"],
            "title": "选项校验测试",
            "options": options,
        },
    )
    assert response.status_code == 422


def test_demo_templates_are_idempotent_and_can_submit(template_client: dict) -> None:
    async def seed_twice() -> None:
        session_factory = template_client["session_factory"]
        async with session_factory() as session:
            await ensure_creation_templates(session, None)
            await session.commit()
            await ensure_creation_templates(session, None)
            await session.commit()

    asyncio.run(seed_twice())

    response = template_client["client"].get(
        "/api/v1/creations/templates",
        params={"pageSize": 100},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    seeded_codes = {"kapok-poster", "lion-dance-poster", "guangcai-poster"}
    assert all(sum(item["code"] == code for item in items) == 1 for code in seeded_codes)

    for template in [item for item in items if item["code"] in seeded_codes]:
        options = {
            name: values[0]
            for name, values in template["options_schema"].items()
        }
        submitted = template_client["client"].post(
            "/api/v1/creations",
            headers=template_client["headers"]["user"],
            json={
                "template_id": template["id"],
                "title": f"{template['name']}测试",
                "options": options,
            },
        )
        assert submitted.status_code == 202

    assert len(template_client["runner"].submitted) == 3


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


def test_system_template_is_hidden_and_free_image_records_request(
    template_client: dict,
) -> None:
    async def seed() -> None:
        async with template_client["session_factory"]() as session:
            await ensure_creation_templates(session, None)
            await session.commit()

    asyncio.run(seed())
    public_items = template_client["client"].get(
        "/api/v1/creations/templates"
    ).json()["data"]["items"]
    admin_items = template_client["client"].get(
        "/api/v1/admin/creation-templates",
        headers=template_client["headers"]["admin"],
        params={"pageSize": 100},
    ).json()["data"]["items"]
    assert SYSTEM_FREE_IMAGE_TEMPLATE_CODE not in {item["code"] for item in public_items}
    assert SYSTEM_FREE_IMAGE_TEMPLATE_CODE not in {item["code"] for item in admin_items}

    for aspect, size in {
        "SQUARE": "1024x1024",
        "PORTRAIT": "768x1344",
        "LANDSCAPE": "1344x768",
    }.items():
        response = template_client["client"].post(
            "/api/v1/creations/free-image",
            headers=template_client["headers"]["user"],
            json={"prompt": "  一座未来感校园建筑  ", "aspectRatio": aspect},
        )
        assert response.status_code == 202
        payload = response.json()["data"]["input_payload"]
        assert payload["user_prompt"] == "一座未来感校园建筑"
        assert payload["_kind"] == "FREE_IMAGE"
        assert payload["_size"] == size


@pytest.mark.parametrize(
    "payload",
    [
        {"prompt": "", "aspectRatio": "SQUARE"},
        {"prompt": "有效提示", "aspectRatio": "WIDE"},
        {"prompt": "长" * 2001, "aspectRatio": "PORTRAIT"},
    ],
)
def test_free_image_validates_input(template_client: dict, payload: dict) -> None:
    response = template_client["client"].post(
        "/api/v1/creations/free-image",
        headers=template_client["headers"]["user"],
        json=payload,
    )
    assert response.status_code == 422


def test_post_draft_requires_login_and_returns_editable_fields(
    template_client: dict,
) -> None:
    unauthenticated = template_client["client"].post(
        "/api/v1/ai/post-drafts",
        json={"prompt": "写一篇校园建筑推文"},
    )
    assert unauthenticated.status_code == 401

    response = template_client["client"].post(
        "/api/v1/ai/post-drafts",
        headers=template_client["headers"]["user"],
        json={"prompt": "写一篇校园建筑推文"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"]
    assert data["content"]
    assert data["tags"]
    assert data["provider"] == "mock"
    assert data["fallbackUsed"] is False
