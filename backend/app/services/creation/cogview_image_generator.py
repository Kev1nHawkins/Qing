"""智谱 CogView-4 图片生成 Adapter。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.services.creation.exceptions import (
    ImageGenerationConfigurationError,
    ImageGenerationNetworkError,
    ImageGenerationResponseError,
)
from app.services.creation.image_generator import DEFAULT_OUTPUT_DIR, ImageGeneratorAdapter


CONTENT_TYPE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class CogViewImageGenerator(ImageGeneratorAdapter):
    """调用 CogView-4，并把临时远程图片保存到Qing上传目录。"""

    def __init__(
        self,
        task_id: str,
        api_key: str | None,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "cogview-4-250304",
        size: str = "768x1344",
        quality: str = "standard",
        watermark_enabled: bool = True,
        timeout_seconds: float = 90.0,
        max_retries: int = 2,
        retry_delay_seconds: float = 1.0,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        clean_key = (api_key or "").strip()
        if not clean_key:
            raise ImageGenerationConfigurationError(
                "未配置 ZHIPU_API_KEY，请在项目根目录 .env 中设置该变量"
            )
        if timeout_seconds <= 0:
            raise ImageGenerationConfigurationError(
                "ZHIPU_IMAGE_TIMEOUT_SECONDS 必须大于 0"
            )
        if max_retries < 0:
            raise ImageGenerationConfigurationError(
                "ZHIPU_IMAGE_MAX_RETRIES 不能小于 0"
            )
        if retry_delay_seconds < 0:
            raise ImageGenerationConfigurationError(
                "ZHIPU_IMAGE_RETRY_DELAY_SECONDS 不能小于 0"
            )

        self.task_id = task_id
        self._api_key = clean_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.size = size
        self.quality = quality
        self.watermark_enabled = watermark_enabled
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.output_dir = output_dir
        self._transport = transport

    @classmethod
    def from_settings(
        cls,
        task_id: str,
        settings: Any,
        transport: httpx.BaseTransport | None = None,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
    ) -> "CogViewImageGenerator":
        """从Qing Settings兼容对象创建Adapter；配置字段将在后续阶段合并。"""
        secret = getattr(settings, "zhipu_api_key", None)
        api_key = secret.get_secret_value() if secret is not None else None
        return cls(
            task_id=task_id,
            api_key=api_key,
            base_url=settings.zhipu_base_url,
            model=settings.zhipu_image_model,
            size=settings.zhipu_image_size,
            quality=settings.zhipu_image_quality,
            watermark_enabled=settings.zhipu_image_watermark_enabled,
            timeout_seconds=settings.zhipu_image_timeout_seconds,
            max_retries=settings.zhipu_image_max_retries,
            retry_delay_seconds=settings.zhipu_image_retry_delay_seconds,
            output_dir=output_dir,
            transport=transport,
        )

    def generate(self, prompt: str) -> Path:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("发送给 CogView-4 的 Prompt 不能为空")

        with httpx.Client(
            timeout=self.timeout_seconds,
            transport=self._transport,
            follow_redirects=True,
        ) as client:
            response = self._request_with_retry(
                client,
                "POST",
                f"{self.base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "prompt": clean_prompt,
                    "quality": self.quality,
                    "size": self.size,
                    "watermark_enabled": self.watermark_enabled,
                },
                operation="CogView-4 图片生成",
            )
            image_url = self._extract_image_url(response)
            image_response = self._request_with_retry(
                client,
                "GET",
                image_url,
                operation="CogView-4 图片下载",
            )

        content_type = image_response.headers.get("content-type", "")
        content_type = content_type.split(";", 1)[0].strip().lower()
        extension = CONTENT_TYPE_EXTENSIONS.get(content_type)
        if extension is None:
            raise ImageGenerationResponseError(
                f"CogView-4 返回的文件不是支持的图片类型：{content_type or '未知类型'}"
            )
        if not image_response.content:
            raise ImageGenerationResponseError("CogView-4 返回了空图片")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{self.task_id}{extension}"
        try:
            output_path.write_bytes(image_response.content)
        except OSError as exc:
            raise ImageGenerationResponseError(
                f"CogView-4 图片保存失败：{type(exc).__name__}"
            ) from exc
        return output_path

    def _request_with_retry(
        self,
        client: httpx.Client,
        method: str,
        url: str,
        *,
        operation: str,
        **kwargs: Any,
    ) -> httpx.Response:
        last_network_error: httpx.RequestError | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = client.request(method, url, **kwargs)
            except httpx.RequestError as exc:
                last_network_error = exc
                if attempt < self.max_retries:
                    self._wait_before_retry(attempt)
                    continue
                break

            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt < self.max_retries:
                    self._wait_before_retry(attempt)
                    continue
                raise ImageGenerationResponseError(
                    f"{operation}失败：HTTP {response.status_code}，已重试 "
                    f"{self.max_retries} 次"
                )
            if response.is_error:
                raise ImageGenerationResponseError(
                    f"{operation}失败：HTTP {response.status_code}，"
                    f"{self._safe_error_message(response)}"
                )
            return response

        error_name = (
            type(last_network_error).__name__
            if last_network_error is not None
            else "RequestError"
        )
        raise ImageGenerationNetworkError(
            f"{operation}网络请求失败：{error_name}，已重试 {self.max_retries} 次"
        ) from last_network_error

    def _wait_before_retry(self, attempt: int) -> None:
        delay = self.retry_delay_seconds * (2**attempt)
        if delay > 0:
            time.sleep(delay)

    @staticmethod
    def _extract_image_url(response: httpx.Response) -> str:
        try:
            payload = response.json()
            image_url = payload["data"][0]["url"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ImageGenerationResponseError(
                "CogView-4 API 返回结构无效，缺少图片 URL"
            ) from exc

        if not isinstance(image_url, str) or not image_url.strip():
            raise ImageGenerationResponseError("CogView-4 API 返回了空图片 URL")
        parsed = urlparse(image_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ImageGenerationResponseError("CogView-4 API 返回了无效图片 URL")
        return image_url.strip()

    @staticmethod
    def _safe_error_message(response: httpx.Response) -> str:
        try:
            payload: Any = response.json()
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            message = error.get("message") if isinstance(error, dict) else None
            if isinstance(message, str) and message.strip():
                return message.strip()[:300]
        except ValueError:
            pass
        return "供应商未返回可识别的错误说明"
