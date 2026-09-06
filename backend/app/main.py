from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

configure_logging()
logger = structlog.get_logger(__name__)
UPLOAD_ROOT = Path(__file__).resolve().parents[1] / "uploads"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.environment != "development" and "change" in settings.jwt_secret_key.lower():
        logger.warning("insecure_jwt_secret", message="生产环境必须更换 JWT_SECRET_KEY")
    logger.info("application_started", environment=settings.environment)
    yield
    logger.info("application_stopped")


app = FastAPI(
    title=f"{settings.project_name} API",
    description="岭南文化与校园文化 AI 共创传播平台统一后端",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT, check_dir=False), name="uploads")


@app.get("/health", tags=["System"], summary="服务健康检查")
async def health(request: Request) -> dict:
    return {
        "code": 0,
        "message": "ok",
        "data": {"status": "healthy", "service": settings.project_name},
        "requestId": getattr(request.state, "request_id", str(uuid4())),
    }
