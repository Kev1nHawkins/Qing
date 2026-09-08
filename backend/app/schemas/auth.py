from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas.common import Timestamped


def compact_phone(value: str | None) -> str | None:
    if isinstance(value, str):
        return "".join(value.split())
    return value


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr | None = None
    password: str = Field(min_length=8, max_length=72)
    nickname: str = Field(min_length=1, max_length=64)
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    phone_challenge_id: str | None = Field(default=None, alias="phoneChallengeId")
    phone_code: str | None = Field(default=None, alias="phoneCode", pattern=r"^\d{6}$")

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        return compact_phone(value)

    @model_validator(mode="after")
    def validate_phone_verification(self) -> "RegisterRequest":
        supplied = (self.phone, self.phone_challenge_id, self.phone_code)
        if any(supplied) and not all(supplied):
            raise ValueError("填写手机号时必须同时提供验证码挑战和六位验证码")
        return self


class LoginRequest(BaseModel):
    username: str
    password: str


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


class PhoneCodeRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return compact_phone(value) or ""


class PhoneCodeRead(BaseModel):
    challenge_id: str = Field(alias="challengeId")
    expires_in: int = Field(alias="expiresIn")
    retry_after: int = Field(alias="retryAfter")
    debug_code: str | None = Field(default=None, alias="debugCode")

    model_config = {"populate_by_name": True}


class PasswordResetRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    challenge_id: str = Field(alias="challengeId")
    code: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(alias="newPassword", min_length=8, max_length=72)

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return compact_phone(value) or ""


class PhoneBindRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    challenge_id: str = Field(alias="challengeId")
    code: str = Field(pattern=r"^\d{6}$")

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return compact_phone(value) or ""

