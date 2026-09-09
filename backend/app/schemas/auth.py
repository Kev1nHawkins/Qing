from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import Timestamped


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr | None = None
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    password: str = Field(min_length=8, max_length=72)
    nickname: str = Field(min_length=1, max_length=64)


class LoginRequest(BaseModel):
    username: str
    password: str


class SmsCodeRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    purpose: Literal["REGISTER", "LOGIN", "RESET"]


class SmsLoginRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class PasswordResetRequest(SmsLoginRequest):
    new_password: str = Field(min_length=8, max_length=72)


class RoleRead(BaseModel):
    code: str
    name: str

    model_config = {"from_attributes": True}


class UserRead(Timestamped):
    username: str
    email: EmailStr | None
    phone: str | None
    nickname: str
    avatar_url: str | None
    bio: str | None
    is_active: bool
    points_total: int
    role: RoleRead


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead

