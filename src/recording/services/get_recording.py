import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.recording.repository import RecordingRepository
from src.recording.schema.response import RecordingDetail


async def get_recording_service(
    session: AsyncSession, recording_id: uuid.UUID
) -> RecordingDetail:
    recording = await RecordingRepository(session).get_active(recording_id)
    if recording is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found")
    return RecordingDetail.model_validate(recording)
