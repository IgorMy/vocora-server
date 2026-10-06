import uuid

from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.recording.repository import RecordingRepository
from src.shared.audit_request.log import audit_log


async def delete_recording_service(
    session: AsyncSession, recording_id: uuid.UUID
) -> Response:
    repository = RecordingRepository(session)
    if await repository.get_active(recording_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found")

    await repository.soft_delete(recording_id, actor="request")
    await audit_log("INFO", "Recording deleted", {"recording_id": str(recording_id)})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
