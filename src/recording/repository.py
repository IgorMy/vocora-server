import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.recording.constants import DELETED_FILTER
from src.recording.model import Recording
from src.recording.schema.update import RecordingUpdate
from src.shared.audit_change.constants import ACTOR
from src.shared.audit_change.repository import BaseRepository


class RecordingRepository(BaseRepository[Recording]):
    # process_log grows on every processing step and segments repeats the
    # transcription with timestamps: auditing them would only add noise
    ignored_columns: frozenset[str] = frozenset(
        {"updated_at", "process_log", "segments"}
    )

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Recording)

    async def get(self, recording_id: uuid.UUID) -> Recording | None:
        return await self.session.get(Recording, recording_id)

    async def get_active(self, recording_id: uuid.UUID) -> Recording | None:
        """Like get, but a soft deleted recording counts as missing."""
        recording = await self.get(recording_id)
        return recording if recording and recording.deleted_at is None else None

    async def find(
        self,
        *,
        updated_since: datetime.datetime | None,
        deleted: DELETED_FILTER,
        limit: int,
        offset: int,
    ) -> list[Recording]:
        """
        Ordered by updated_at so a client can sync page by page.
        deleted: "exclude" only active recordings, "include" active and deleted,
        "only" deleted ones.
        """
        query = select(Recording)
        if updated_since is not None:
            query = query.where(col(Recording.updated_at) > updated_since)
        if deleted == "exclude":
            query = query.where(col(Recording.deleted_at).is_(None))
        elif deleted == "only":
            query = query.where(col(Recording.deleted_at).is_not(None))
        result = await self.session.execute(
            query.order_by(col(Recording.updated_at), col(Recording.id))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars())

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

    async def soft_delete(self, recording_id: uuid.UUID, *, actor: ACTOR) -> None:
        await self._update(
            recording_id,
            {"deleted_at": datetime.datetime.now(tz=datetime.UTC)},
            actor=actor,
        )
