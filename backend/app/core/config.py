from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "岭潮共创"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "mysql+asyncmy://lingchao:lingchao_dev@mysql:3306/lingchao?charset=utf8mb4"
    )
    jwt_secret_key: str = "dev-secret-change-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    admin_username: str = "admin"
    admin_password: str = "Admin123!"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

