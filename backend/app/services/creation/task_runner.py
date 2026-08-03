"""基于ai_creations数据库记录的后台图片生成执行器。"""

from __future__ import annotations

import asyncio
from concurrent.futures import Executor
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.creation import AICreation
from app.models.enums import CreationStatus
from app.services.creation.content_service import CreationContentService
from app.services.creation.exceptions import ImageGenerationError
from app.services.creation.image_generator import ImageGeneratorAdapter
from app.services.creation.provider_factory import create_image_generator


GeneratorFactory = Callable[[str], ImageGeneratorAdapter]


class CreationTaskRunner:
    """调度生成任务，任务状态的唯一来源是ai_creations表。"""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
        generator_factory: GeneratorFactory = create_image_generator,
        executor: Executor | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.generator_factory = generator_factory
        self.executor = executor
        self._background_tasks: set[asyncio.Task[None]] = set()

    def submit(self, creation_id: int) -> None:
        task = asyncio.create_task(
            self.process(creation_id),
            name=f"ai-creation-{creation_id}",
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def process(self, creation_id: int) -> None:
        """原子认领PENDING记录，并推进到SUCCESS或FAILED。"""
        claimed = await self._claim_pending(creation_id)
        if claimed is None:
            return

        try:
            base_prompt, input_payload = claimed
            settings = get_settings()
            content = await CreationContentService(settings).generate(
                base_prompt=base_prompt,
                options=input_payload,
            )
            generation = self._generation_metadata(content.metadata(), settings)
            await self._store_generation_plan(
                creation_id,
                visual_prompt=content.visual_prompt,
                description=content.cultural_description,
                input_payload={**input_payload, "_generation": generation},
            )
            generator = self.generator_factory(f"creation_{creation_id}")
            generated_path = await asyncio.get_running_loop().run_in_executor(
                self.executor,
                generator.generate,
                content.visual_prompt,
            )
            output_url = self._to_output_url(generated_path)
        except ImageGenerationError as exc:
            await self._mark_failed(creation_id, self._safe_error_message(exc))
            return
        except Exception as exc:
            await self._mark_failed(
                creation_id,
                f"图片生成失败：{type(exc).__name__}",
            )
            return

        async with self.session_factory() as session:
            await session.execute(
                update(AICreation)
                .where(
                    AICreation.id == creation_id,
                    AICreation.status == CreationStatus.PROCESSING.value,
                )
                .values(
                    status=CreationStatus.SUCCESS.value,
                    output_url=output_url,
                    error_message=None,
                )
            )
            await session.commit()

    async def _claim_pending(
        self,
        creation_id: int,
    ) -> tuple[str, dict[str, Any]] | None:
        async with self.session_factory() as session:
            result = await session.execute(
                update(AICreation)
                .where(
                    AICreation.id == creation_id,
                    AICreation.status == CreationStatus.PENDING.value,
                )
                .values(
                    status=CreationStatus.PROCESSING.value,
                    error_message=None,
                )
            )
            if result.rowcount != 1:
                await session.rollback()
                return None
            await session.commit()
            row = (
                await session.execute(
                    select(AICreation.prompt, AICreation.input_payload).where(
                        AICreation.id == creation_id
                    )
                )
            ).one()
            return row.prompt, dict(row.input_payload or {})

    async def _store_generation_plan(
        self,
        creation_id: int,
        *,
        visual_prompt: str,
        description: str,
        input_payload: dict[str, Any],
    ) -> None:
        async with self.session_factory() as session:
            await session.execute(
                update(AICreation)
                .where(
                    AICreation.id == creation_id,
                    AICreation.status == CreationStatus.PROCESSING.value,
                )
                .values(
                    prompt=visual_prompt,
                    description=description,
                    input_payload=input_payload,
                )
            )
            await session.commit()

    async def _mark_failed(self, creation_id: int, error_message: str) -> None:
        async with self.session_factory() as session:
            await session.execute(
                update(AICreation)
                .where(
                    AICreation.id == creation_id,
                    AICreation.status == CreationStatus.PROCESSING.value,
                )
                .values(
                    status=CreationStatus.FAILED.value,
                    output_url=None,
                    error_message=error_message[:500],
                )
            )
            await session.commit()

    @staticmethod
    def _to_output_url(generated_path: Path) -> str:
        return f"/uploads/ai-generated/{generated_path.name}"

    @staticmethod
    def _generation_metadata(content: dict[str, Any], settings: Any) -> dict[str, Any]:
        image_provider = settings.image_generator_provider.strip().lower()
        text_provider = str(content["text_provider"])
        if image_provider in {"cogview", "zhipu"}:
            generation_mode = "AI_IMAGE"
            image_source = "external_image_provider"
            provider = image_provider
            model = settings.zhipu_image_model
        elif text_provider == "deepseek" and not content["fallback_used"]:
            generation_mode = "AI_TEXT_TEMPLATE"
            image_source = "local_svg_template"
            provider = "deepseek"
            model = content["text_model"]
        else:
            generation_mode = "MOCK_TEMPLATE"
            image_source = "local_svg_template"
            provider = "mock"
            model = "local-template-v2"

        return {
            "provider": provider,
            "generationMode": generation_mode,
            "model": model,
            "imageSource": image_source,
            "fallbackUsed": bool(content["fallback_used"]),
            "visualPrompt": content["visual_prompt"],
            "generatedTitle": content["title"],
            "subtitle": content["subtitle"],
            "tags": content["tags"],
            "suggestedPalette": content["suggested_palette"],
            "layoutHint": content["layout_hint"],
            "textProvider": text_provider,
            "textModel": content["text_model"],
            "imageProvider": image_provider,
        }

    @staticmethod
    def _safe_error_message(exc: ImageGenerationError) -> str:
        message = str(exc).strip()
        return message[:500] if message else "图片生成失败"


@lru_cache
def get_creation_task_runner() -> CreationTaskRunner:
    return CreationTaskRunner()
