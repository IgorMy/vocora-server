import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.recording.constants import DELETED_FILTER
from src.recording.repository import RecordingRepository
from src.recording.schema.response import RecordingPage, RecordingSummary


async def list_recording_service(
    session: AsyncSession,
    updated_since: datetime.datetime | None,
    deleted: DELETED_FILTER,
    limit: int,
    offset: int,
) -> RecordingPage:
    # One extra row tells whether there is a next page without a COUNT query
    recordings = await RecordingRepository(session).find(
        updated_since=updated_since, deleted=deleted, limit=limit + 1, offset=offset
    )
    return RecordingPage(
        items=[RecordingSummary.model_validate(r) for r in recordings[:limit]],
        next_offset=offset + limit if len(recordings) > limit else None,
    )
