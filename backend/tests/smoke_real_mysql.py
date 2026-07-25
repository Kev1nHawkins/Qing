"""Real-MySQL HTTP smoke test for the competition demo path."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

BASE_URL = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000")
USE_TESTCLIENT = os.getenv("SMOKE_USE_TESTCLIENT") == "1"
results: list[dict] = []


def compact(data):
    if isinstance(data, dict):
        keys = (
            "id",
            "username",
            "pointsTotal",
            "awardedPoints",
            "alreadyCompleted",
            "alreadyStarted",
            "liked",
            "likeCount",
            "alreadyLiked",
            "total",
            "userCount",
        )
        selected = {key: data[key] for key in keys if key in data}
        return selected or {"keys": list(data)[:8]}
    if isinstance(data, list):
        return {"count": len(data)}
    return data


def call(
    client: httpx.Client,
    name: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    expected_status: int = 200,
    **kwargs,
) -> dict:
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = client.request(method, path, headers=headers, **kwargs)
    try:
        payload = response.json()
    except ValueError:
        payload = {"code": None, "message": response.text[:200], "data": None}
    passed = response.status_code == expected_status
    if expected_status < 400:
        passed = passed and payload.get("code") == 0
    result = {
        "name": name,
        "method": method,
        "path": path,
        "http": response.status_code,
        "code": payload.get("code"),
        "message": payload.get("message"),
        "keyData": compact(payload.get("data")),
        "result": "PASS" if passed else "FAIL",
    }
    results.append(result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if not passed:
        raise AssertionError(f"{name} failed: {result}")
    return payload


def main() -> None:
    if USE_TESTCLIENT:
        from fastapi.testclient import TestClient

        from app.main import app

        client_context = TestClient(app, base_url=BASE_URL)
    else:
        client_context = httpx.Client(base_url=BASE_URL, timeout=10.0)

    with client_context as client:
        call(client, "health", "GET", "/health")

        suffix = uuid4().hex[:10]
        username = f"smoke_{suffix}"
        password = "Smoke123!"
        call(
            client,
            "register",
            "POST",
            "/api/v1/auth/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": password,
                "nickname": "冒烟测试用户",
            },
        )
        user_login = call(
            client,
            "user_login",
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        user_token = user_login["data"]["access_token"]
        call(client, "current_user", "GET", "/api/v1/auth/me", token=user_token)

        cultures = call(client, "culture_list", "GET", "/api/v1/cultures")
        culture_id = cultures["data"]["items"][0]["id"]
        call(client, "culture_detail", "GET", f"/api/v1/cultures/{culture_id}")

        routes = call(client, "route_list", "GET", "/api/v1/routes")
        route_id = routes["data"]["items"][0]["id"]
        route_detail = call(
            client, "route_detail", "GET", f"/api/v1/routes/{route_id}"
        )
        task_id = route_detail["data"]["tasks"][0]["id"]
        call(
            client,
            "route_start",
            "POST",
            f"/api/v1/routes/{route_id}/start",
            token=user_token,
        )
        call(
            client,
            "task_complete_without_photo_denied",
            "POST",
            f"/api/v1/tasks/{task_id}/complete",
            token=user_token,
            json={},
            expected_status=400,
        )
        call(
            client,
            "fake_image_upload_denied",
            "POST",
            "/api/v1/uploads/images",
            token=user_token,
            files={"file": ("fake.png", b"not-an-image", "image/png")},
            expected_status=400,
        )
        upload = call(
            client,
            "task_photo_upload",
            "POST",
            "/api/v1/uploads/images",
            token=user_token,
            files={
                "file": (
                    "checkin.png",
                    (
                        b"\x89PNG\r\n\x1a\n"
                        b"\x00\x00\x00\rIHDR"
                        b"\x00\x00\x00\x01\x00\x00\x00\x01"
                        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
                    ),
                    "image/png",
                )
            },
            expected_status=201,
        )

        first_complete = call(
            client,
            "task_complete",
            "POST",
            f"/api/v1/tasks/{task_id}/complete",
            token=user_token,
            json={"answer": f"PHOTO:{upload['data']['url']}"},
        )
        first_total = first_complete["data"]["pointsTotal"]
        route_progress = call(
            client,
            "route_progress_with_photo",
            "GET",
            f"/api/v1/routes/{route_id}/progress",
            token=user_token,
        )
        completed_record = next(
            record
            for record in route_progress["data"]["records"]
            if record["taskId"] == task_id
        )
        if not (completed_record.get("answer") or "").startswith("PHOTO:/uploads/"):
            raise AssertionError("route progress did not expose the user's photo footprint")
        points = call(
            client,
            "points_records",
            "GET",
            "/api/v1/points/records",
            token=user_token,
        )
        duplicate_complete = call(
            client,
            "task_complete_duplicate",
            "POST",
            f"/api/v1/tasks/{task_id}/complete",
            token=user_token,
            json={},
        )
        if not duplicate_complete["data"]["alreadyCompleted"]:
            raise AssertionError("duplicate task completion was not reported as idempotent")
        if points["data"]["total"] != 1:
            raise AssertionError("task completion created duplicate point records")
        me_after = call(
            client, "current_user_after_task", "GET", "/api/v1/auth/me", token=user_token
        )
        if me_after["data"]["points_total"] != first_total:
            raise AssertionError("duplicate task completion changed point total")
        shop = call(client, "point_shop", "GET", "/api/v1/points/shop")
        if len(shop["data"]["products"]) < 8:
            raise AssertionError("point shop product catalog is not diverse enough")
        redemption_id = f"smoke-{suffix}"
        redemption = call(
            client,
            "point_shop_redeem",
            "POST",
            "/api/v1/points/redeem",
            token=user_token,
            json={
                "product_code": "kapok-wallpaper",
                "redemption_id": redemption_id,
            },
        )
        if redemption["data"]["pointsTotal"] != 0:
            raise AssertionError("point redemption did not deduct the expected balance")
        duplicate_redemption = call(
            client,
            "point_shop_redeem_duplicate",
            "POST",
            "/api/v1/points/redeem",
            token=user_token,
            json={
                "product_code": "kapok-wallpaper",
                "redemption_id": redemption_id,
            },
        )
        if not duplicate_redemption["data"]["alreadyRedeemed"]:
            raise AssertionError("duplicate redemption was not idempotent")
        redemptions = call(
            client,
            "point_shop_redemptions",
            "GET",
            "/api/v1/points/redemptions",
            token=user_token,
        )
        if redemptions["data"]["total"] != 1:
            raise AssertionError("redemption inventory did not return the redeemed product")
        redemption_item = redemptions["data"]["items"][0]
        if redemption_item["productCode"] != "kapok-wallpaper":
            raise AssertionError("redemption inventory returned the wrong product")
        if redemption_item["status"] != "AVAILABLE" or not redemption_item["voucherCode"]:
            raise AssertionError("redemption inventory did not return a usable voucher")

        post = call(
            client,
            "community_post_create",
            "POST",
            "/api/v1/community/posts",
            token=user_token,
            json={
                "title": "红棉寻迹冒烟作品",
                "content": "这是一条用于真实 MySQL 冒烟测试的社区帖子。",
                "culture_item_id": culture_id,
                "tags": [],
            },
            expected_status=201,
        )
        post_id = post["data"]["id"]
        first_like = call(
            client,
            "post_like",
            "POST",
            f"/api/v1/community/posts/{post_id}/like",
            token=user_token,
        )
        second_like = call(
            client,
            "post_like_duplicate",
            "POST",
            f"/api/v1/community/posts/{post_id}/like",
            token=user_token,
        )
        if first_like["data"]["likeCount"] != second_like["data"]["likeCount"]:
            raise AssertionError("duplicate like changed like count")
        if not second_like["data"]["alreadyLiked"]:
            raise AssertionError("duplicate like was not reported as idempotent")

        call(
            client,
            "normal_user_admin_denied",
            "GET",
            "/api/v1/admin/dashboard",
            token=user_token,
            expected_status=403,
        )
        admin_login = call(
            client,
            "admin_login",
            "POST",
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin123!"},
        )
        call(
            client,
            "admin_dashboard",
            "GET",
            "/api/v1/admin/dashboard",
            token=admin_login["data"]["access_token"],
        )

    print(
        json.dumps(
            {"summary": {"passed": len(results), "failed": 0, "total": len(results)}},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "summary": {
                        "passed": sum(item["result"] == "PASS" for item in results),
                        "failed": 1,
                        "total": len(results),
                    },
                    "error": str(exc),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise
