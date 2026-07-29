"""基于ai_creations数据库记录的后台图片生成执行器。"""

from __future__ import annotations

import asyncio
from concurrent.futures import Executor, ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from typing import Callable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import AsyncSessionLocal
from app.models.creation import AICreation
from app.models.enums import CreationStatus
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
        self.executor = executor or ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="ai-creation",
        )

    def submit(self, creation_id: int) -> None:
        self.executor.submit(self._run_in_worker, creation_id)

    def _run_in_worker(self, creation_id: int) -> None:
        asyncio.run(self.process(creation_id))

    async def process(self, creation_id: int) -> None:
        """原子认领PENDING记录，并推进到SUCCESS或FAILED。"""
        prompt = await self._claim_pending(creation_id)
        if prompt is None:
            return

        try:
            generator = self.generator_factory(f"creation_{creation_id}")
            generated_path = generator.generate(prompt)
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

    async def _claim_pending(self, creation_id: int) -> str | None:
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
            return await session.scalar(
                select(AICreation.prompt).where(AICreation.id == creation_id)
            )

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
    def _safe_error_message(exc: ImageGenerationError) -> str:
        message = str(exc).strip()
        return message[:500] if message else "图片生成失败"


@lru_cache
def get_creation_task_runner() -> CreationTaskRunner:
    return CreationTaskRunner()
