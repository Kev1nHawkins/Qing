from fastapi import APIRouter, HTTPException
from sqlalchemy import or_, select

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import settings
from app.core.response import success
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    SmsCodeRequest,
    SmsLoginRequest,
    TokenRead,
    UserRead,
)
from app.services.verification import verification_service

router = APIRouter(prefix="/auth", tags=["Auth"])


def token_data(user: User) -> dict:
    token = create_access_token(str(user.id), role=user.role.code)
    data = TokenRead(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )
    return data.model_dump()


def verify_code(phone: str, purpose: str, code: str) -> None:
    try:
        verification_service.verify(phone, purpose, code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sms/send", summary="获取手机验证码")
async def send_sms_code(payload: SmsCodeRequest, db: DbSession) -> dict:
    if settings.sms_mode != "demo":
        raise HTTPException(status_code=503, detail="短信服务尚未配置")
    user = await db.scalar(select(User).where(User.phone == payload.phone))
    if payload.purpose == "REGISTER" and user:
        raise HTTPException(status_code=409, detail="该手机号已绑定账号")
    if payload.purpose in {"LOGIN", "RESET"} and not user:
        raise HTTPException(status_code=404, detail="该手机号尚未注册")
    try:
        code, expires_in = verification_service.issue(payload.phone, payload.purpose)
    except ValueError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return success(
        {
            "mode": "DEMO",
            "expiresIn": expires_in,
            "retryAfter": settings.sms_retry_after_seconds,
            "demoCode": code,
        },
        message="演示验证码已生成",
    )


@router.post("/register", summary="用户注册")
async def register(payload: RegisterRequest, db: DbSession) -> dict:
    existing = await db.scalar(
        select(User).where(
            or_(
                User.username == payload.username,
                User.email == payload.email if payload.email else False,
                User.phone == payload.phone,
            )
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="用户名、邮箱或手机号已存在")
    verify_code(payload.phone, "REGISTER", payload.verification_code)
    role = await db.scalar(select(Role).where(Role.code == "user"))
    if not role:
        raise HTTPException(status_code=500, detail="默认角色尚未初始化")
    user = User(
        username=payload.username,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        role_id=role.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return success(token_data(user))


@router.post("/login", summary="JWT 登录")
async def login(payload: LoginRequest, db: DbSession) -> dict:
    user = await db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")
    return success(token_data(user))


@router.post("/sms/login", summary="手机验证码登录")
async def sms_login(payload: SmsLoginRequest, db: DbSession) -> dict:
    user = await db.scalar(select(User).where(User.phone == payload.phone))
    if not user:
        raise HTTPException(status_code=401, detail="手机号或验证码错误")
    verify_code(payload.phone, "LOGIN", payload.verification_code)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")
    return success(token_data(user))


@router.post("/password/reset", summary="手机验证码重置密码")
async def reset_password(payload: PasswordResetRequest, db: DbSession) -> dict:
    user = await db.scalar(select(User).where(User.phone == payload.phone))
    if not user:
        raise HTTPException(status_code=400, detail="手机号或验证码错误")
    verify_code(payload.phone, "RESET", payload.verification_code)
    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return success(message="密码已重置，请使用新密码登录")


@router.get("/me", summary="当前用户信息")
async def me(current_user: CurrentUser) -> dict:
    return success(UserRead.model_validate(current_user).model_dump())

