"""DeepSeek Chat Completions API 适配器。"""

from __future__ import annotations

from typing import Any

import httpx

from app.services.ai.llm_service import (
    LLMAdapter,
    LLMConfigurationError,
    LLMNetworkError,
    LLMResponseError,
)


class DeepSeekLLM(LLMAdapter):
    """使用 deepseek-chat 模型的异步 LLM Adapter。"""

    MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: str | None,
        base_url: str = "https://api.deepseek.com",
        timeout_seconds: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        clean_key = (api_key or "").strip()
        if not clean_key:
            raise LLMConfigurationError(
                "未配置DEEPSEEK_API_KEY，请在项目根目录.env中设置该变量"
            )
        if timeout_seconds <= 0:
            raise LLMConfigurationError("DEEPSEEK_TIMEOUT_SECONDS必须大于0")

        self._api_key = clean_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._transport = transport

    @classmethod
    def from_settings(
        cls,
        settings: Any,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> "DeepSeekLLM":
        """从Qing Settings兼容对象创建Adapter；配置字段将在后续阶段合并。"""
        secret = getattr(settings, "deepseek_api_key", None)
        api_key = secret.get_secret_value() if secret is not None else None
        return cls(
            api_key=api_key,
            base_url=settings.deepseek_base_url,
            timeout_seconds=settings.deepseek_timeout_seconds,
            transport=transport,
        )

    async def generate(self, prompt: str) -> str:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("发送给DeepSeek的Prompt不能为空")

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    "/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.MODEL,
                        "messages": [{"role": "user", "content": clean_prompt}],
                        "stream": False,
                        "temperature": 0,
                    },
                )
        except httpx.RequestError as exc:
            raise LLMNetworkError(f"DeepSeek网络请求失败: {type(exc).__name__}") from exc

        if response.is_error:
            message = self._safe_error_message(response)
            raise LLMResponseError(
                f"DeepSeek API返回错误（HTTP {response.status_code}）: {message}"
            )

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError("DeepSeek API返回结构无效，缺少回答内容") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMResponseError("DeepSeek API返回了空回答")
        return content.strip()

    @staticmethod
    def _safe_error_message(response: httpx.Response) -> str:
        """只提取供应商错误说明，避免把请求头或密钥写入日志。"""
        try:
            payload: Any = response.json()
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            message = error.get("message") if isinstance(error, dict) else None
            if isinstance(message, str) and message.strip():
                return message.strip()[:300]
        except ValueError:
            pass
        return "供应商未返回可识别的错误说明"
