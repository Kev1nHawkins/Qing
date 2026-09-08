import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.base import Base
from app.models.user import PhoneVerificationChallenge, Role, User


@pytest.fixture
def auth_client(tmp_path: Path) -> Iterator[dict]:
    database_path = (tmp_path / "phone-auth.db").resolve().as_posix()
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    state: dict[str, int | str] = {}
    previous_environment = settings.environment
    previous_provider = settings.phone_verification_provider
    previous_resend = settings.phone_code_resend_seconds
    settings.environment = "test"
    settings.phone_verification_provider = "mock"
    settings.phone_code_resend_seconds = 0

    async def prepare() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            role = Role(code="user", name="普通用户")
            session.add(role)
            await session.flush()
            user = User(
                username="phone_owner",
                email="owner@example.com",
                phone="13800138000",
                password_hash=hash_password("OldPassword123!"),
                nickname="手机号用户",
                role_id=role.id,
            )
            unbound = User(
                username="unbound",
                email="unbound@example.com",
                password_hash=hash_password("Unbound123!"),
                nickname="未绑定用户",
                role_id=role.id,
            )
            session.add_all([user, unbound])
            await session.flush()
            state.update({"user_id": user.id, "unbound_id": unbound.id})
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
    with TestClient(app) as client:
        yield {"client": client, "state": state, "session_factory": session_factory}
    app.dependency_overrides.clear()
    settings.environment = previous_environment
    settings.phone_verification_provider = previous_provider
    settings.phone_code_resend_seconds = previous_resend
    asyncio.run(engine.dispose())


def request_code(client: TestClient, path: str, phone: str, headers: dict | None = None) -> dict:
    response = client.post(path, json={"phone": phone}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["debugCode"] and len(data["debugCode"]) == 6
    return data


def test_password_reset_changes_password_and_revokes_old_token(auth_client: dict) -> None:
    client = auth_client["client"]
    old_token = create_access_token(str(auth_client["state"]["user_id"]), role="user")
    code = request_code(client, "/api/v1/auth/password-reset/code", "13800138000")

    reset = client.post(
        "/api/v1/auth/password-reset",
        json={
            "phone": "13800138000",
            "challengeId": code["challengeId"],
            "code": code["debugCode"],
            "newPassword": "NewPassword123!",
        },
    )
    assert reset.status_code == 200
    assert reset.json()["message"] == "密码已重置，请重新登录"
    assert client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {old_token}"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"username": "phone_owner", "password": "OldPassword123!"},
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"username": "phone_owner", "password": "NewPassword123!"},
    ).status_code == 200
    replay = client.post(
        "/api/v1/auth/password-reset",
        json={
            "phone": "13800138000",
            "challengeId": code["challengeId"],
            "code": code["debugCode"],
            "newPassword": "AnotherPassword123!",
        },
    )
    assert replay.status_code == 422


def test_unknown_phone_response_matches_known_phone(auth_client: dict) -> None:
    client = auth_client["client"]
    known = client.post("/api/v1/auth/password-reset/code", json={"phone": "13800138000"})
    unknown = client.post("/api/v1/auth/password-reset/code", json={"phone": "13900139000"})
    assert known.status_code == unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]


def test_registration_phone_requires_and_consumes_verification(auth_client: dict) -> None:
    client = auth_client["client"]
    invalid = client.post(
        "/api/v1/auth/register",
        json={
            "username": "missing_code",
            "nickname": "缺验证码",
            "password": "Register123!",
            "phone": "13700137000",
        },
    )
    assert invalid.status_code == 422
    code = request_code(client, "/api/v1/auth/register/phone-code", "13700137000")
    created = client.post(
        "/api/v1/auth/register",
        json={
            "username": "phone_register",
            "nickname": "手机注册",
            "password": "Register123!",
            "phone": "13700137000",
            "phoneChallengeId": code["challengeId"],
            "phoneCode": code["debugCode"],
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["data"]["user"]["phone"] == "13700137000"

    without_phone = client.post(
        "/api/v1/auth/register",
        json={
            "username": "no_phone_register",
            "nickname": "传统注册",
            "password": "Register123!",
        },
    )
    assert without_phone.status_code == 200
    assert without_phone.json()["data"]["user"]["phone"] is None


def test_authenticated_user_can_bind_phone(auth_client: dict) -> None:
    client = auth_client["client"]
    token = create_access_token(str(auth_client["state"]["unbound_id"]), role="user")
    headers = {"Authorization": f"Bearer {token}"}
    code = request_code(
        client, "/api/v1/auth/me/phone-code", "13600136000", headers=headers
    )
    response = client.put(
        "/api/v1/auth/me/phone",
        headers=headers,
        json={
            "phone": "13600136000",
            "challengeId": code["challengeId"],
            "code": code["debugCode"],
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["phone"] == "13600136000"


def test_challenges_do_not_store_plain_phone_or_code(auth_client: dict) -> None:
    client = auth_client["client"]
    code = request_code(client, "/api/v1/auth/password-reset/code", "13911112222")

    async def verify_storage() -> None:
        async with auth_client["session_factory"]() as session:
            challenge = await session.scalar(
                select(PhoneVerificationChallenge).where(
                    PhoneVerificationChallenge.id == code["challengeId"]
                )
            )
            assert challenge is not None
            assert "13911112222" not in challenge.phone_hash
            assert code["debugCode"] not in challenge.code_hash

    asyncio.run(verify_storage())


def test_wrong_code_is_locked_after_five_attempts(auth_client: dict) -> None:
    client = auth_client["client"]
    data = request_code(client, "/api/v1/auth/password-reset/code", "13800138000")
    payload = {
        "phone": "13800138000",
        "challengeId": data["challengeId"],
        "code": "000000" if data["debugCode"] != "000000" else "000001",
        "newPassword": "NeverApplied123!",
    }
    for _ in range(5):
        assert client.post("/api/v1/auth/password-reset", json=payload).status_code == 422
    payload["code"] = data["debugCode"]
    assert client.post("/api/v1/auth/password-reset", json=payload).status_code == 422


def test_mock_provider_is_rejected_in_production(auth_client: dict) -> None:
    client = auth_client["client"]
    settings.environment = "production"
    try:
        response = client.post(
            "/api/v1/auth/password-reset/code", json={"phone": "13800138000"}
        )
    finally:
        settings.environment = "test"
    assert response.status_code == 503
    assert response.json()["data"] is None
    assert "短信服务" in response.json()["message"]
