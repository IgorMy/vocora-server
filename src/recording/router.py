import datetime
import uuid
from typing import Annotated

from fastapi import Depends, Query, Request, Response
from fastapi.params import File
from fastapi.routing import APIRouter

from src.recording.constants import DELETED_FILTER
from src.recording.schema.request import UploadRecordingRequest
from src.recording.schema.response import RecordingDetail, RecordingPage
from src.recording.services.delete_recording import delete_recording_service
from src.recording.services.get_recording import get_recording_service
from src.recording.services.list_recording import list_recording_service
from src.recording.services.upload_recording import upload_recording_service
from src.shared.auth import require_token
from src.shared.database.engine import SessionDep
from src.shared.rate_limit import limiter

router = APIRouter(
    prefix="/recording",
    tags=["recording"],
    dependencies=[
        Depends(require_token),
    ],
)


@router.post(
    path="",
    summary="Upload a recording. After it is uploaded, it will be added to the process queue.",
    status_code=201,
    response_class=Response,
    responses={
        201: {"description": "Recording uploaded successfully"},
        200: {"description": "Recording already exists"},
        400: {"description": "Invalid request"},
        429: {"description": "Too many requests"},
    },
)
@limiter.limit("10/minute")  # pyright: ignore[reportUntypedFunctionDecorator, reportUnknownMemberType]
async def upload_recording(
    request: Request,  # pyright: ignore[reportUnusedParameter]  # required by slowapi
    data: Annotated[UploadRecordingRequest, File()],
    session: SessionDep,
):
    return await upload_recording_service(data, session)


@router.get(
    path="",
    summary="List recordings, ordered by last update, to keep the app in sync.",
    description=(
        "`updated_since` returns only the recordings changed after that moment. "
        "`deleted` chooses which ones come back: `exclude` (default) only the "
        "active ones, `include` also the deleted ones (`deleted_at` set), `only` "
        "just the deleted ones. To sync, use `updated_since` with `deleted=include` "
        "so the app also learns which recordings to remove. "
        "Keep requesting with `offset=next_offset` until `next_offset` is null."
    ),
)
async def list_recording(
    session: SessionDep,
    updated_since: datetime.datetime | None = None,
    deleted: DELETED_FILTER = "exclude",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RecordingPage:
    return await list_recording_service(session, updated_since, deleted, limit, offset)


@router.get(
    path="/{recording_id}",
    summary="Get a recording with its transcription.",
    responses={404: {"description": "Recording not found or deleted"}},
)
async def get_recording(
    recording_id: uuid.UUID, session: SessionDep
) -> RecordingDetail:
    return await get_recording_service(session, recording_id)


@router.delete(
    path="/{recording_id}",
    summary="Delete a recording. It is a soft delete: its data and audio files are kept.",
    status_code=204,
    response_class=Response,
    responses={404: {"description": "Recording not found or already deleted"}},
)
async def delete_recording(recording_id: uuid.UUID, session: SessionDep) -> Response:
    return await delete_recording_service(session, recording_id)
