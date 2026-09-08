from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import PhoneVerificationChallenge
from app.services.sms_provider import get_sms_provider

REGISTER_PHONE = "REGISTER_PHONE"
PASSWORD_RESET = "PASSWORD_RESET"
BIND_PHONE = "BIND_PHONE"


def normalize_phone(phone: str) -> str:
    return "".join(phone.split())


def _digest(value: str) -> str:
    return hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _phone_digest(phone: str) -> str:
    return _digest(f"phone:{phone}")


def _code_digest(challenge_id: str, code: str) -> str:
    return _digest(f"code:{challenge_id}:{code}")


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


async def issue_phone_code(
    db: AsyncSession,
    *,
    phone: str,
    purpose: str,
    user_id: int | None,
) -> dict[str, str | int | None]:
    now = datetime.now(UTC)
    phone_hash = _phone_digest(phone)
    latest = await db.scalar(
        select(PhoneVerificationChallenge)
        .where(
            PhoneVerificationChallenge.phone_hash == phone_hash,
            PhoneVerificationChallenge.purpose == purpose,
        )
        .order_by(PhoneVerificationChallenge.created_at.desc())
        .limit(1)
    )
    if latest and _as_utc(latest.created_at) > now - timedelta(
        seconds=settings.phone_code_resend_seconds
    ):
        raise HTTPException(status_code=429, detail="验证码发送过于频繁，请稍后再试")

    sent_last_hour = await db.scalar(
        select(func.count(PhoneVerificationChallenge.id)).where(
            PhoneVerificationChallenge.phone_hash == phone_hash,
            PhoneVerificationChallenge.purpose == purpose,
            PhoneVerificationChallenge.created_at >= now - timedelta(hours=1),
        )
    )
    if int(sent_last_hour or 0) >= settings.phone_code_hourly_limit:
        raise HTTPException(status_code=429, detail="验证码发送次数已达上限，请稍后再试")

    challenge_id = str(uuid4())
    code = f"{secrets.randbelow(1_000_000):06d}"
    debug_code = await get_sms_provider().send_code(phone=phone, code=code)
    challenge = PhoneVerificationChallenge(
        id=challenge_id,
        purpose=purpose,
        phone_hash=phone_hash,
        user_id=user_id,
        code_hash=_code_digest(challenge_id, code),
        expires_at=now + timedelta(seconds=settings.phone_code_expire_seconds),
    )
    db.add(challenge)
    await db.commit()
    return {
        "challengeId": challenge_id,
        "expiresIn": settings.phone_code_expire_seconds,
        "retryAfter": settings.phone_code_resend_seconds,
        "debugCode": debug_code,
    }


async def verify_phone_code(
    db: AsyncSession,
    *,
    challenge_id: str,
    phone: str,
    code: str,
    purpose: str,
    user_id: int | None = None,
) -> PhoneVerificationChallenge:
    challenge = await db.scalar(
        select(PhoneVerificationChallenge)
        .where(PhoneVerificationChallenge.id == challenge_id)
        .with_for_update()
    )
    now = datetime.now(UTC)
    invalid = (
        not challenge
        or challenge.purpose != purpose
        or challenge.phone_hash != _phone_digest(phone)
        or challenge.consumed_at is not None
        or _as_utc(challenge.expires_at) <= now
        or challenge.failed_attempts >= settings.phone_code_max_attempts
        or (user_id is not None and challenge.user_id != user_id)
    )
    if invalid:
        raise HTTPException(status_code=422, detail="验证码无效或已过期")

    if not hmac.compare_digest(challenge.code_hash, _code_digest(challenge_id, code)):
        challenge.failed_attempts += 1
        await db.commit()
        raise HTTPException(status_code=422, detail="验证码无效或已过期")

    challenge.consumed_at = now
    return challenge
