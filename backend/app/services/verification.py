from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import randbelow
from threading import Lock

from app.core.config import settings


@dataclass
class VerificationCode:
    digest: str
    expires_at: datetime
    retry_at: datetime
    attempts_left: int = 5


class DemoVerificationService:
    """Process-local verification codes for the competition demo environment."""

    def __init__(self) -> None:
        self._codes: dict[tuple[str, str], VerificationCode] = {}
        self._lock = Lock()

    @staticmethod
    def _digest(phone: str, purpose: str, code: str) -> str:
        value = f"{settings.jwt_secret_key}:{phone}:{purpose}:{code}"
        return sha256(value.encode("utf-8")).hexdigest()

    def issue(self, phone: str, purpose: str) -> tuple[str, int]:
        now = datetime.now(UTC)
        key = (phone, purpose)
        with self._lock:
            current = self._codes.get(key)
            if current and current.retry_at > now:
                wait_seconds = max(1, int((current.retry_at - now).total_seconds()))
                raise ValueError(f"请在 {wait_seconds} 秒后重新获取验证码")
            code = f"{randbelow(1_000_000):06d}"
            self._codes[key] = VerificationCode(
                digest=self._digest(phone, purpose, code),
                expires_at=now + timedelta(seconds=settings.sms_code_expire_seconds),
                retry_at=now + timedelta(seconds=settings.sms_retry_after_seconds),
            )
        return code, settings.sms_code_expire_seconds

    def verify(self, phone: str, purpose: str, code: str) -> None:
        now = datetime.now(UTC)
        key = (phone, purpose)
        with self._lock:
            current = self._codes.get(key)
            if not current or current.expires_at <= now or current.attempts_left <= 0:
                self._codes.pop(key, None)
                raise ValueError("验证码无效或已过期，请重新获取")
            if current.digest != self._digest(phone, purpose, code):
                current.attempts_left -= 1
                raise ValueError("验证码错误")
            self._codes.pop(key, None)


verification_service = DemoVerificationService()
