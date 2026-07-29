import os
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./member4-test-bootstrap.sqlite3")

from app.api.dependencies import get_current_user
from app.api.points import SHOP_PRODUCTS
from app.api.task import distance_meters, validate_task_configuration
from app.core.database import get_db
from app.main import app
from app.models import Base, FileAsset, Location, Role, Route, RouteTask, User
from app.schemas.points import PointRedeemRequest
from app.schemas.route import TaskCompleteRequest, TaskCreate, TaskRead
from app.services.task_evidence import resolve_asset_path, validate_image


def minimal_png(width: int = 1, height: int = 1) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
        + b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_member4_schema_and_file_validation(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    assert "qr_code" not in TaskRead.model_fields
    assert distance_meters(23.039, 113.370, 23.039, 113.370) == 0
    assert 100 < distance_meters(23.039, 113.370, 23.041, 113.370) < 300

    TaskCompleteRequest(latitude=90, longitude=180, file_asset_id=1)
    with pytest.raises(ValidationError):
        TaskCompleteRequest(latitude=91)
    with pytest.raises(ValidationError):
        TaskCreate(
            route_id=1,
            location_id=1,
            order_no=1,
            title="越界定位任务",
            description="测试",
            task_type="SIMULATED_LOCATION",
            latitude=91,
            longitude=113,
        )
    with pytest.raises(ValidationError):
        TaskCreate(
            route_id=1,
            location_id=1,
            order_no=1,
            title="过大范围任务",
            description="测试",
            task_type="SIMULATED_LOCATION",
            latitude=23,
            longitude=113,
            radius_meters=1001,
        )
    with pytest.raises(ValidationError):
        PointRedeemRequest(product_code="kapok-wallpaper", redemption_id="../../etc")
    with pytest.raises(HTTPException) as missing_qr:
        validate_task_configuration(RouteTask(task_type="QR_CODE", qr_code=None))
    assert missing_qr.value.status_code == 422
    with pytest.raises(HTTPException) as missing_location:
        validate_task_configuration(
            RouteTask(task_type="SIMULATED_LOCATION", latitude=None, longitude=None)
        )
    assert missing_location.value.status_code == 422

    validate_image(minimal_png(), "image/png")
    with pytest.raises(HTTPException):
        validate_image(minimal_png() + b"<script>", "image/png")
    with pytest.raises(HTTPException):
        validate_image(minimal_png(10_000, 10_000), "image/png")

    monkeypatch.setenv("LINGCHAO_UPLOAD_ROOT", str(tmp_path))
    with pytest.raises(HTTPException):
        resolve_asset_path("../outside.png")
    assert len({product["code"] for product in SHOP_PRODUCTS}) == len(SHOP_PRODUCTS)


@pytest.mark.asyncio
async def test_member4_task_evidence_ownership_and_task_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("LINGCHAO_UPLOAD_ROOT", str(tmp_path))
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        role = Role(code="user", name="用户", description=None)
        session.add(role)
        await session.flush()
        user = User(
            username="member4-user",
            email=None,
            password_hash="unused",
            nickname="成员4测试",
            avatar_url=None,
            bio=None,
            is_active=True,
            points_total=0,
            role_id=role.id,
        )
        other_user = User(
            username="other-user",
            email=None,
            password_hash="unused",
            nickname="其他用户",
            avatar_url=None,
            bio=None,
            is_active=True,
            points_total=0,
            role_id=role.id,
        )
        session.add_all([user, other_user])
        await session.flush()
        location = Location(
            name="测试地点",
            address="广州大学",
            description=None,
            latitude=Decimal("23.0390000"),
            longitude=Decimal("113.3700000"),
            image_url=None,
            culture_item_id=None,
        )
        route = Route(
            title="安全测试路线",
            slug="member4-security-route",
            summary="成员4独立测试",
            cover_image_url=None,
            duration_minutes=30,
            distance_km=Decimal("1.00"),
            status="PUBLISHED",
            created_by_id=None,
        )
        draft_route = Route(
            title="未发布测试路线",
            slug="member4-draft-route",
            summary="不应公开",
            cover_image_url=None,
            duration_minutes=30,
            distance_km=Decimal("1.00"),
            status="DRAFT",
            created_by_id=None,
        )
        session.add_all([location, route, draft_route])
        await session.flush()
        photo_task = RouteTask(
            route_id=route.id,
            culture_item_id=None,
            location_id=location.id,
            order_no=1,
            title="图片任务",
            description="上传图片",
            task_type="CHECK_IN",
            question=None,
            options=None,
            correct_answer=None,
            points=10,
            qr_code=None,
            latitude=None,
            longitude=None,
            radius_meters=100,
        )
        qr_task = RouteTask(
            route_id=route.id,
            culture_item_id=None,
            location_id=location.id,
            order_no=2,
            title="二维码任务",
            description="校验二维码",
            task_type="QR_CODE",
            question=None,
            options=None,
            correct_answer=None,
            points=10,
            qr_code="SERVER-ONLY-CODE",
            latitude=None,
            longitude=None,
            radius_meters=100,
        )
        location_task = RouteTask(
            route_id=route.id,
            culture_item_id=None,
            location_id=location.id,
            order_no=3,
            title="定位任务",
            description="校验位置",
            task_type="SIMULATED_LOCATION",
            question=None,
            options=None,
            correct_answer=None,
            points=10,
            qr_code=None,
            latitude=Decimal("23.0390000"),
            longitude=Decimal("113.3700000"),
            radius_meters=100,
        )
        draft_task = RouteTask(
            route_id=draft_route.id,
            culture_item_id=None,
            location_id=location.id,
            order_no=1,
            title="未发布任务",
            description="不应公开",
            task_type="QUIZ",
            question="未发布问题",
            options=["A", "B"],
            correct_answer="A",
            points=10,
            qr_code=None,
            latitude=None,
            longitude=None,
            radius_meters=100,
        )
        session.add_all([photo_task, qr_task, location_task, draft_task])
        await session.commit()
        ids = {
            "user": user.id,
            "other_user": other_user.id,
            "route": route.id,
            "draft_route": draft_route.id,
            "draft_task": draft_task.id,
            "photo": photo_task.id,
            "qr": qr_task.id,
            "location": location_task.id,
        }

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    async def override_user() -> User:
        async with session_factory() as session:
            current = await session.get(User, ids["user"])
            assert current is not None
            return current

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            route_list_response = await client.get("/api/v1/routes")
            assert route_list_response.status_code == 200
            assert route_list_response.json()["data"]["total"] == 1
            draft_route_response = await client.get(f"/api/v1/routes/{ids['draft_route']}")
            assert draft_route_response.status_code == 404

            task_list_response = await client.get("/api/v1/tasks")
            assert task_list_response.status_code == 200
            assert task_list_response.json()["data"]["total"] == 3
            draft_task_response = await client.get(f"/api/v1/tasks/{ids['draft_task']}")
            assert draft_task_response.status_code == 404

            route_response = await client.get(f"/api/v1/routes/{ids['route']}")
            assert route_response.status_code == 200
            assert "qr_code" not in route_response.text
            assert "SERVER-ONLY-CODE" not in route_response.text

            unstarted_upload_response = await client.post(
                f"/api/v1/tasks/{ids['photo']}/evidence",
                content=minimal_png(),
                headers={"Content-Type": "image/png", "X-File-Name": "checkin.png"},
            )
            assert unstarted_upload_response.status_code == 409

            start_response = await client.post(f"/api/v1/routes/{ids['route']}/start")
            assert start_response.status_code == 200

            upload_response = await client.post(
                f"/api/v1/tasks/{ids['photo']}/evidence",
                content=minimal_png(),
                headers={"Content-Type": "image/png", "X-File-Name": "checkin.png"},
            )
            assert upload_response.status_code == 201
            asset_id = upload_response.json()["data"]["id"]

            async with session_factory() as session:
                extra_assets = [
                    FileAsset(
                        owner_id=ids["user"],
                        original_name=f"extra-{index}.png",
                        storage_key=f"task-checkins/extra-{index}.png",
                        public_url=(
                            f"/api/v1/tasks/{ids['photo']}/evidence/pending"
                        ),
                        mime_type="image/png",
                        size_bytes=1,
                        usage_type=f"TASK_CHECKIN:{ids['photo']}",
                    )
                    for index in range(4)
                ]
                session.add_all(
                    extra_assets
                )
                foreign_asset = FileAsset(
                    owner_id=ids["other_user"],
                    original_name="foreign.png",
                    storage_key="task-checkins/foreign.png",
                    public_url=f"/api/v1/tasks/{ids['photo']}/evidence/pending",
                    mime_type="image/png",
                    size_bytes=1,
                    usage_type=f"TASK_CHECKIN:{ids['photo']}",
                )
                wrong_task_asset = FileAsset(
                    owner_id=ids["user"],
                    original_name="wrong-task.png",
                    storage_key="task-checkins/wrong-task.png",
                    public_url=f"/api/v1/tasks/{ids['qr']}/evidence/pending",
                    mime_type="image/png",
                    size_bytes=1,
                    usage_type=f"TASK_CHECKIN:{ids['qr']}",
                )
                session.add_all([foreign_asset, wrong_task_asset])
                await session.commit()
                missing_file_asset_id = extra_assets[0].id
                foreign_asset_id = foreign_asset.id
                wrong_task_asset_id = wrong_task_asset.id

            capped_upload_response = await client.post(
                f"/api/v1/tasks/{ids['photo']}/evidence",
                content=minimal_png(),
                headers={"Content-Type": "image/png", "X-File-Name": "checkin.png"},
            )
            assert capped_upload_response.status_code == 429

            forged_response = await client.post(
                f"/api/v1/tasks/{ids['photo']}/complete",
                json={"file_asset_id": foreign_asset_id},
            )
            assert forged_response.status_code == 400
            wrong_task_response = await client.post(
                f"/api/v1/tasks/{ids['photo']}/complete",
                json={"file_asset_id": wrong_task_asset_id},
            )
            assert wrong_task_response.status_code == 400
            missing_file_response = await client.post(
                f"/api/v1/tasks/{ids['photo']}/complete",
                json={"file_asset_id": missing_file_asset_id},
            )
            assert missing_file_response.status_code == 404

            complete_response = await client.post(
                f"/api/v1/tasks/{ids['photo']}/complete",
                json={"file_asset_id": asset_id},
            )
            assert complete_response.status_code == 200
            assert complete_response.json()["data"]["awardedPoints"] == 10

            repeat_response = await client.post(
                f"/api/v1/tasks/{ids['photo']}/complete",
                json={"file_asset_id": asset_id},
            )
            assert repeat_response.status_code == 200
            assert repeat_response.json()["data"]["alreadyCompleted"] is True

            redemption_payload = {
                "product_code": "kapok-wallpaper",
                "redemption_id": "request_0001",
            }
            redeem_response = await client.post(
                "/api/v1/points/redeem",
                json=redemption_payload,
            )
            assert redeem_response.status_code == 200
            assert redeem_response.json()["data"]["pointsTotal"] == 0

            async with session_factory() as session:
                updated_user = await session.get(User, ids["user"])
                assert updated_user is not None
                updated_user.points_total = 15
                await session.commit()

            retry_redeem_response = await client.post(
                "/api/v1/points/redeem",
                json=redemption_payload,
            )
            assert retry_redeem_response.status_code == 200
            assert retry_redeem_response.json()["data"]["alreadyRedeemed"] is True
            assert retry_redeem_response.json()["data"]["pointsTotal"] == 15

            second_once_response = await client.post(
                "/api/v1/points/redeem",
                json={
                    "product_code": "kapok-wallpaper",
                    "redemption_id": "request_0002",
                },
            )
            assert second_once_response.status_code == 409

            wrong_qr_response = await client.post(
                f"/api/v1/tasks/{ids['qr']}/complete",
                json={"qr_code": "WRONG"},
            )
            assert wrong_qr_response.status_code == 400
            correct_qr_response = await client.post(
                f"/api/v1/tasks/{ids['qr']}/complete",
                json={"qr_code": "SERVER-ONLY-CODE"},
            )
            assert correct_qr_response.status_code == 200

            far_location_response = await client.post(
                f"/api/v1/tasks/{ids['location']}/complete",
                json={"latitude": 23.05, "longitude": 113.37},
            )
            assert far_location_response.status_code == 400
            near_location_response = await client.post(
                f"/api/v1/tasks/{ids['location']}/complete",
                json={"latitude": 23.039, "longitude": 113.37},
            )
            assert near_location_response.status_code == 200
            assert near_location_response.json()["data"]["distanceMeters"] == 0

            evidence_response = await client.get(
                f"/api/v1/tasks/{ids['photo']}/evidence/{asset_id}"
            )
            assert evidence_response.status_code == 200
            assert evidence_response.headers["x-content-type-options"] == "nosniff"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
