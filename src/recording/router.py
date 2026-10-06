from typing import Annotated

from fastapi import Depends, Request, Response
from fastapi.params import File
from fastapi.routing import APIRouter

from src.recording.schema.request import UploadRecordingRequest
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
