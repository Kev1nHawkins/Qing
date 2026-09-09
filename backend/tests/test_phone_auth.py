from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.database import get_db
from app.main import app
from app.models.base import Base
from app.models.user import Role


@pytest.fixture
def phone_auth_client(tmp_path: Path) -> Iterator[TestClient]:
    database_path = (tmp_path / "phone-auth.db").resolve().as_posix()
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def prepare() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            session.add(Role(code="user", name="普通用户"))
            await session.commit()

    asyncio.run(prepare())

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def get_demo_code(client: TestClient, phone: str, purpose: str) -> str:
    response = client.post(
        "/api/v1/auth/sms/send",
        json={"phone": phone, "purpose": purpose},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["requestId"]
    assert payload["data"]["mode"] == "DEMO"
    return payload["data"]["demoCode"]


def test_demo_phone_registration_login_and_password_reset(phone_auth_client: TestClient) -> None:
    phone = "13800138001"
    register_code = get_demo_code(phone_auth_client, phone, "REGISTER")
    registration = phone_auth_client.post(
        "/api/v1/auth/register",
        json={
            "username": "phone-user",
            "nickname": "手机用户",
            "email": None,
            "phone": phone,
            "verification_code": register_code,
            "password": "Password123!",
        },
    )
    assert registration.status_code == 200
    assert registration.json()["data"]["user"]["phone"] == phone

    password_login = phone_auth_client.post(
        "/api/v1/auth/login",
        json={"username": "phone-user", "password": "Password123!"},
    )
    assert password_login.status_code == 200

    login_code = get_demo_code(phone_auth_client, phone, "LOGIN")
    sms_login = phone_auth_client.post(
        "/api/v1/auth/sms/login",
        json={"phone": phone, "verification_code": login_code},
    )
    assert sms_login.status_code == 200
    assert sms_login.json()["data"]["access_token"]
    reused_code = phone_auth_client.post(
        "/api/v1/auth/sms/login",
        json={"phone": phone, "verification_code": login_code},
    )
    assert reused_code.status_code == 400

    reset_code = get_demo_code(phone_auth_client, phone, "RESET")
    reset = phone_auth_client.post(
        "/api/v1/auth/password/reset",
        json={
            "phone": phone,
            "verification_code": reset_code,
            "new_password": "Changed123!",
        },
    )
    assert reset.status_code == 200
    assert phone_auth_client.post(
        "/api/v1/auth/login",
        json={"username": "phone-user", "password": "Password123!"},
    ).status_code == 401
    assert phone_auth_client.post(
        "/api/v1/auth/login",
        json={"username": "phone-user", "password": "Changed123!"},
    ).status_code == 200


def test_registration_requires_valid_phone_and_code(phone_auth_client: TestClient) -> None:
    response = phone_auth_client.post(
        "/api/v1/auth/register",
        json={
            "username": "missing-phone",
            "nickname": "缺少手机号",
            "password": "Password123!",
        },
    )
    assert response.status_code == 422
