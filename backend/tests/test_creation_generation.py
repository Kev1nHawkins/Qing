"""Qing现有Creation接口与AI图片生成后台流程测试。"""

from __future__ import annotations

import asyncio
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.main import app
from app.models import Base
from app.models.creation import CreationTemplate
from app.models.enums import PublishStatus
from app.services.creation.exceptions import ImageGenerationResponseError
from app.services.creation.image_generator import ImageGeneratorAdapter, MockImageGenerator
from app.services.creation.task_runner import CreationTaskRunner, get_creation_task_runner


class HoldingExecutor:
    def submit(self, fn: Any, /, *args: Any, **kwargs: Any) -> Future[Any]:
        return Future()


class FailingImageGenerator(ImageGeneratorAdapter):
    def generate(self, prompt: str) -> Path:
        raise ImageGenerationResponseError("模拟图片供应商失败")


class SwitchableGeneratorFactory:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.should_fail = False

    def __call__(self, task_id: str) -> ImageGeneratorAdapter:
        if self.should_fail:
            return FailingImageGenerator()
        return MockImageGenerator(task_id=task_id, output_dir=self.output_dir)


class CreationHarness:
    def __init__(
        self,
        client: TestClient,
        runner: CreationTaskRunner,
        generator_factory: SwitchableGeneratorFactory,
        template_id: int,
    ) -> None:
        self.client = client
        self.runner = runner
        self.generator_factory = generator_factory
        self.template_id = template_id

    def create(self) -> dict:
        response = self.client.post(
            "/api/v1/creations",
            json={
                "template_id": self.template_id,
                "title": "木棉文化海报",
                "options": {
                    "culture_element": "木棉文化",
                    "campus_landmark": "广州大学",
                    "style": "国潮风",
                },
            },
        )
        assert response.status_code == 202
        return response.json()["data"]

    def get(self, creation_id: int) -> dict:
        response = self.client.get(f"/api/v1/creations/{creation_id}")
        assert response.status_code == 200
        return response.json()["data"]

    def process(self, creation_id: int) -> None:
        asyncio.run(self.runner.process(creation_id))


@pytest.fixture
def creation_harness(
    tmp_path: Path,
) -> Any:
    database_path = tmp_path / "creation-test.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path.as_posix()}",
        poolclass=NullPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def prepare_database() -> int:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            template = CreationTemplate(
                name="测试海报模板",
                code="test-poster",
                description="测试模板",
                prompt_template="以{culture_element}和{campus_landmark}为主题，创作{style}海报。",
                options_schema={
                    "culture_element": ["木棉文化"],
                    "campus_landmark": ["广州大学"],
                    "style": ["国潮风"],
                },
                preview_url=None,
                status=PublishStatus.PUBLISHED.value,
                culture_item_id=None,
            )
            session.add(template)
            await session.commit()
            await session.refresh(template)
            return template.id

    template_id = asyncio.run(prepare_database())
    generator_factory = SwitchableGeneratorFactory(tmp_path / "generated")
    runner = CreationTaskRunner(
        session_factory=session_factory,
        generator_factory=generator_factory,
        executor=HoldingExecutor(),
    )

    async def override_get_db() -> Any:
        async with session_factory() as session:
            yield session

    async def override_current_user() -> Any:
        return SimpleNamespace(
            id=1,
            role=SimpleNamespace(code="user"),
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_creation_task_runner] = lambda: runner
    try:
        with TestClient(app) as client:
            yield CreationHarness(client, runner, generator_factory, template_id)
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_creation_task_runner, None)
        asyncio.run(engine.dispose())


def test_create_ai_generation_task_persists_input(
    creation_harness: CreationHarness,
) -> None:
    creation = creation_harness.create()

    assert creation["id"] > 0
    assert creation["input_payload"] == {
        "culture_element": "木棉文化",
        "campus_landmark": "广州大学",
        "style": "国潮风",
    }
    assert "木棉文化" in creation["prompt"]
    assert creation["retry_count"] == 0


def test_new_creation_is_pending(creation_harness: CreationHarness) -> None:
    creation = creation_harness.create()

    assert creation["status"] == "PENDING"
    assert creation["output_url"] is None
    assert creation["error_message"] is None


def test_mock_generation_reaches_success(creation_harness: CreationHarness) -> None:
    creation = creation_harness.create()
    creation_harness.process(creation["id"])

    completed = creation_harness.get(creation["id"])
    assert completed["status"] == "SUCCESS"
    assert completed["output_url"].endswith(f"/creation_{creation['id']}.svg")
    assert completed["error_message"] is None


def test_generation_failure_is_persisted(creation_harness: CreationHarness) -> None:
    creation_harness.generator_factory.should_fail = True
    creation = creation_harness.create()
    creation_harness.process(creation["id"])

    failed = creation_harness.get(creation["id"])
    assert failed["status"] == "FAILED"
    assert failed["output_url"] is None
    assert failed["error_message"] == "模拟图片供应商失败"


def test_failed_creation_can_retry_to_success(
    creation_harness: CreationHarness,
) -> None:
    creation_harness.generator_factory.should_fail = True
    creation = creation_harness.create()
    creation_harness.process(creation["id"])
    assert creation_harness.get(creation["id"])["status"] == "FAILED"

    creation_harness.generator_factory.should_fail = False
    retry_response = creation_harness.client.post(
        f"/api/v1/creations/{creation['id']}/retry"
    )
    assert retry_response.status_code == 200
    retry_data = retry_response.json()["data"]
    assert retry_data["status"] == "PENDING"
    assert retry_data["retry_count"] == 1
    assert retry_data["error_message"] is None

    creation_harness.process(creation["id"])
    completed = creation_harness.get(creation["id"])
    assert completed["status"] == "SUCCESS"
    assert completed["retry_count"] == 1
