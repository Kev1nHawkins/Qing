from typing import Protocol

from fastapi import HTTPException

from app.core.config import settings


class SmsProvider(Protocol):
    async def send_code(self, *, phone: str, code: str) -> str | None: ...


class MockSmsProvider:
    async def send_code(self, *, phone: str, code: str) -> str | None:
        del phone
        if settings.environment.lower() not in {"development", "test"}:
            raise HTTPException(status_code=503, detail="生产环境短信服务尚未配置")
        return code


def get_sms_provider() -> SmsProvider:
    if settings.phone_verification_provider.lower() == "mock":
        return MockSmsProvider()
    raise HTTPException(status_code=503, detail="短信服务尚未配置")
