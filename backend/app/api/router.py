from fastapi import APIRouter

from app.api import (
    admin,
    auth,
    badge,
    community,
    creation,
    culture,
    location,
    points,
    route,
    task,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(culture.router)
api_router.include_router(location.router)
api_router.include_router(route.router)
api_router.include_router(task.router)
api_router.include_router(creation.router)
api_router.include_router(community.router)
api_router.include_router(points.router)
api_router.include_router(badge.router)
api_router.include_router(admin.router)
