from fastapi import APIRouter

from src.recording.router import router as recording_router

router = APIRouter()
router.include_router(recording_router)
