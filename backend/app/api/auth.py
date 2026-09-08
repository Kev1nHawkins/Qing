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
    PhoneBindRequest,
    PhoneCodeRead,
    PhoneCodeRequest,
    RegisterRequest,
    TokenRead,
    UserRead,
)
from app.services.phone_verification import (
    BIND_PHONE,
    PASSWORD_RESET,
    REGISTER_PHONE,
    issue_phone_code,
    normalize_phone,
    verify_phone_code,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", summary="用户注册")
async def register(payload: RegisterRequest, db: DbSession) -> dict:
    phone = normalize_phone(payload.phone) if payload.phone else None
    existing = await db.scalar(
        select(User).where(
            or_(
                User.username == payload.username,
                User.email == payload.email if payload.email else False,
                User.phone == phone if phone else False,
            )
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="用户名、邮箱或手机号已存在")
    if phone:
        await verify_phone_code(
            db,
            challenge_id=payload.phone_challenge_id or "",
            phone=phone,
            code=payload.phone_code or "",
            purpose=REGISTER_PHONE,
        )
    role = await db.scalar(select(Role).where(Role.code == "user"))
    if not role:
        raise HTTPException(status_code=500, detail="默认角色尚未初始化")
    user = User(
        username=payload.username,
        email=payload.email,
        phone=phone,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        role_id=role.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id), role=role.code, auth_version=user.auth_version)
    data = TokenRead(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )
    return success(data.model_dump())


@router.post("/login", summary="JWT 登录")
async def login(payload: LoginRequest, db: DbSession) -> dict:
    user = await db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")
    token = create_access_token(
        str(user.id), role=user.role.code, auth_version=user.auth_version
    )
    data = TokenRead(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )
    return success(data.model_dump())


@router.get("/me", summary="当前用户信息")
async def me(current_user: CurrentUser) -> dict:
    return success(UserRead.model_validate(current_user).model_dump())


@router.post("/register/phone-code", summary="发送注册手机号验证码")
async def register_phone_code(payload: PhoneCodeRequest, db: DbSession) -> dict:
    phone = normalize_phone(payload.phone)
    if await db.scalar(select(User.id).where(User.phone == phone)):
        raise HTTPException(status_code=409, detail="该手机号已绑定其他账号")
    data = await issue_phone_code(
        db,
        phone=phone,
        purpose=REGISTER_PHONE,
        user_id=None,
    )
    return success(
        PhoneCodeRead.model_validate(data).model_dump(by_alias=True),
        "验证码已发送",
    )


@router.post("/password-reset/code", summary="发送找回密码验证码")
async def password_reset_code(payload: PhoneCodeRequest, db: DbSession) -> dict:
    phone = normalize_phone(payload.phone)
    user = await db.scalar(select(User).where(User.phone == phone, User.is_active.is_(True)))
    data = await issue_phone_code(
        db,
        phone=phone,
        purpose=PASSWORD_RESET,
        user_id=user.id if user else None,
    )
    return success(
        PhoneCodeRead.model_validate(data).model_dump(by_alias=True),
        "如果该手机号已绑定账号，验证码已发送",
    )


@router.post("/password-reset", summary="手机号验证码重置密码")
async def password_reset(payload: PasswordResetRequest, db: DbSession) -> dict:
    phone = normalize_phone(payload.phone)
    challenge = await verify_phone_code(
        db,
        challenge_id=payload.challenge_id,
        phone=phone,
        code=payload.code,
        purpose=PASSWORD_RESET,
    )
    if challenge.user_id is not None:
        user = await db.scalar(select(User).where(User.id == challenge.user_id))
        if user and user.is_active:
            user.password_hash = hash_password(payload.new_password)
            user.auth_version += 1
    await db.commit()
    return success(message="密码已重置，请重新登录")


@router.post("/me/phone-code", summary="发送绑定手机号验证码")
async def me_phone_code(
    payload: PhoneCodeRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    phone = normalize_phone(payload.phone)
    owner_id = await db.scalar(select(User.id).where(User.phone == phone))
    if owner_id is not None and owner_id != current_user.id:
        raise HTTPException(status_code=409, detail="该手机号已绑定其他账号")
    data = await issue_phone_code(
        db,
        phone=phone,
        purpose=BIND_PHONE,
        user_id=current_user.id,
    )
    return success(
        PhoneCodeRead.model_validate(data).model_dump(by_alias=True),
        "验证码已发送",
    )


@router.put("/me/phone", summary="绑定或更换手机号")
async def update_me_phone(
    payload: PhoneBindRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    phone = normalize_phone(payload.phone)
    owner_id = await db.scalar(select(User.id).where(User.phone == phone))
    if owner_id is not None and owner_id != current_user.id:
        raise HTTPException(status_code=409, detail="该手机号已绑定其他账号")
    await verify_phone_code(
        db,
        challenge_id=payload.challenge_id,
        phone=phone,
        code=payload.code,
        purpose=BIND_PHONE,
        user_id=current_user.id,
    )
    current_user.phone = phone
    await db.commit()
    await db.refresh(current_user)
    return success(UserRead.model_validate(current_user).model_dump(), "手机号已更新")

