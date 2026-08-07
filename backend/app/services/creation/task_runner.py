"""基于ai_creations数据库记录的后台图片生成执行器。"""

from __future__ import annotations

import asyncio
from concurrent.futures import Executor
from functools import lru_cache
import logging
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.models.creation import AICreation
from app.models.enums import CreationStatus
from app.services.creation.content_service import CreationContentService
from app.services.creation.exceptions import ImageGenerationError
from app.services.creation.image_generator import ImageGeneratorAdapter, MockImageGenerator
from app.services.creation.provider_factory import create_image_generator


GeneratorFactory = Callable[[str], ImageGeneratorAdapter]
logger = logging.getLogger(__name__)


def create_mock_image_generator(task_id: str) -> ImageGeneratorAdapter:
    return MockImageGenerator(task_id=task_id)


class CreationTaskRunner:
    """调度生成任务，任务状态的唯一来源是ai_creations表。"""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
        generator_factory: GeneratorFactory = create_image_generator,
        executor: Executor | None = None,
        fallback_generator_factory: GeneratorFactory = create_mock_image_generator,
        settings: Settings | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.generator_factory = generator_factory
        self.executor = executor
        self.fallback_generator_factory = fallback_generator_factory
        self.settings = settings
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
            settings = self.settings or get_settings()
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
            task_id = f"creation_{creation_id}"
            try:
                generated_path = await self._generate_image(
                    self.generator_factory,
                    task_id,
                    content.visual_prompt,
                )
            except ImageGenerationError as exc:
                if not self._uses_external_image_provider(settings):
                    raise
                generated_path = await self._generate_mock_fallback(
                    creation_id=creation_id,
                    task_id=task_id,
                    prompt=content.visual_prompt,
                    provider=settings.image_generator_provider,
                    external_error=exc,
                )
                generation = self._mock_fallback_metadata(generation)
                await self._store_generation_plan(
                    creation_id,
                    visual_prompt=content.visual_prompt,
                    description=content.cultural_description,
                    input_payload={**input_payload, "_generation": generation},
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

    async def _generate_image(
        self,
        factory: GeneratorFactory,
        task_id: str,
        prompt: str,
    ) -> Path:
        generator = factory(task_id)
        return await asyncio.get_running_loop().run_in_executor(
            self.executor,
            generator.generate,
            prompt,
        )

    async def _generate_mock_fallback(
        self,
        *,
        creation_id: int,
        task_id: str,
        prompt: str,
        provider: str,
        external_error: ImageGenerationError,
    ) -> Path:
        logger.warning(
            "External image generation failed; using mock fallback: "
            "creation_id=%s provider=%s error_type=%s error=%s",
            creation_id,
            provider,
            type(external_error).__name__,
            self._safe_error_message(external_error),
        )
        try:
            generated_path = await self._generate_image(
                self.fallback_generator_factory,
                task_id,
                prompt,
            )
        except Exception as fallback_error:
            fallback_message = self._safe_error_message(fallback_error)
            logger.error(
                "Mock image fallback failed: creation_id=%s "
                "error_type=%s error=%s",
                creation_id,
                type(fallback_error).__name__,
                fallback_message,
            )
            raise ImageGenerationError(
                f"Mock降级图片生成失败：{fallback_message}"
            ) from fallback_error

        logger.info(
            "Mock image fallback succeeded: creation_id=%s output=%s",
            creation_id,
            generated_path.name,
        )
        return generated_path

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
    def _mock_fallback_metadata(generation: dict[str, Any]) -> dict[str, Any]:
        return {
            **generation,
            "provider": "mock",
            "generationMode": "MOCK_TEMPLATE",
            "model": "local-template-v2",
            "imageSource": "local_svg_template",
            "fallbackUsed": True,
            "imageProvider": "mock",
        }

    @staticmethod
    def _uses_external_image_provider(settings: Any) -> bool:
        return settings.image_generator_provider.strip().lower() in {"cogview", "zhipu"}

    @staticmethod
    def _safe_error_message(exc: Exception) -> str:
        message = str(exc).strip()
        return message[:500] if message else "图片生成失败"


@lru_cache
def get_creation_task_runner() -> CreationTaskRunner:
    return CreationTaskRunner()
