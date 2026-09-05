"""根据Qing配置创建图片生成Adapter。"""

from app.core.config import Settings, get_settings
from app.services.creation.cogview_image_generator import CogViewImageGenerator
from app.services.creation.exceptions import ImageGenerationConfigurationError
from app.services.creation.image_generator import ImageGeneratorAdapter, MockImageGenerator


def create_image_generator(
    task_id: str,
    settings: Settings | None = None,
    size: str | None = None,
) -> ImageGeneratorAdapter:
    resolved_settings = settings or get_settings()
    provider = resolved_settings.image_generator_provider.strip().lower()
    if provider == "mock":
        return MockImageGenerator(task_id=task_id, size=size or "768x1344")
    if provider in {"cogview", "zhipu"}:
        return CogViewImageGenerator.from_settings(
            task_id=task_id,
            settings=resolved_settings,
            size=size,
        )
    raise ImageGenerationConfigurationError(
        f"不支持的IMAGE_GENERATOR_PROVIDER: "
        f"{resolved_settings.image_generator_provider}"
    )
