from fastapi import APIRouter

from src.health.server_router import router as server_router

router = APIRouter(prefix="/health", tags=["health"])
router.include_router(server_router)
