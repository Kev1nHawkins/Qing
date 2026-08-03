from functools import lru_cache
from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    llm_provider: str = "mock"
    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_temperature: float = 0.7
    deepseek_timeout_seconds: float = 30.0
    image_generator_provider: str = "mock"
    zhipu_api_key: SecretStr | None = None
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_image_model: str = "cogview-4-250304"
    zhipu_image_size: str = "768x1344"
    zhipu_image_quality: str = "standard"
    zhipu_image_watermark_enabled: bool = True
    zhipu_image_timeout_seconds: float = 90.0
    zhipu_image_max_retries: int = 2
    zhipu_image_retry_delay_seconds: float = 1.0
    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    embedding_device: str = "cpu"
    embedding_cache_dir: str = "work/model-cache"
    rag_knowledge_dir: str = "data/knowledge_base"
    rag_prompt_path: str = "data/prompts/rag_chat.txt"
    image_prompt_path: str = "data/prompts/image_prompt.txt"
    rag_vector_store_dir: str = "work/chroma"
    rag_collection_name: str = "lingnan_knowledge"
    rag_top_k: int = 5
    rag_min_score: float = 0.45
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

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
