from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import Timestamped


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr | None = None
    password: str = Field(min_length=8, max_length=72)
    nickname: str = Field(min_length=1, max_length=64)


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

