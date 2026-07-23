from fastapi import APIRouter, HTTPException
from sqlalchemy import or_, select

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import settings
from app.core.response import success
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenRead, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", summary="用户注册")
async def register(payload: RegisterRequest, db: DbSession) -> dict:
    existing = await db.scalar(
        select(User).where(
            or_(
                User.username == payload.username,
                User.email == payload.email if payload.email else False,
            )
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")
    role = await db.scalar(select(Role).where(Role.code == "user"))
    if not role:
        raise HTTPException(status_code=500, detail="默认角色尚未初始化")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        role_id=role.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id), role=role.code)
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
    token = create_access_token(str(user.id), role=user.role.code)
    data = TokenRead(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )
    return success(data.model_dump())


@router.get("/me", summary="当前用户信息")
async def me(current_user: CurrentUser) -> dict:
    return success(UserRead.model_validate(current_user).model_dump())

