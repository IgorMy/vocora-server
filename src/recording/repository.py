import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.recording.model import Recording
from src.recording.schema.update import RecordingUpdate
from src.shared.audit_change.constants import ACTOR
from src.shared.audit_change.repository import BaseRepository


class RecordingRepository(BaseRepository[Recording]):
    # process_log grows on every processing step, auditing it would only add noise
    ignored_columns: frozenset[str] = frozenset({"updated_at", "process_log"})

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Recording)

    async def get(self, recording_id: uuid.UUID) -> Recording | None:
        return await self.session.get(Recording, recording_id)

    async def get_by_folder(self, folder: str) -> Recording | None:
        result = await self.session.execute(
            select(Recording).where(col(Recording.folder) == folder)
        )
        return result.scalar_one_or_none()

    async def create(self, recording: Recording, *, actor: ACTOR) -> Recording:
        return await self._create(recording, actor=actor)

    async def update(
        self, recording_id: uuid.UUID, data: RecordingUpdate, *, actor: ACTOR
    ) -> None:
        """Updates only the fields that were explicitly set in `data`."""
        await self._update(
            recording_id, data.model_dump(exclude_unset=True), actor=actor
        )
