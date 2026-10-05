import uuid

from sqlalchemy import literal, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.shared.audit.model import AuditRequest, LogEntry
from src.shared.audit.schema import AuditRequestUpdate


class AuditRequestRepository:
    """
    Persists request audits. Every method commits right away, so it must get its
    own session: the audit has to survive a rollback of the request it records,
    and logs must reach the database even if the process dies mid-request.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def create(self, audit_request: AuditRequest) -> AuditRequest:
        self.session.add(audit_request)
        await self.session.commit()
        return audit_request

    async def update(
        self, audit_request_id: uuid.UUID, data: AuditRequestUpdate
    ) -> None:
        """Updates only the fields that were explicitly set in `data`."""
        values = data.model_dump(mode="json", exclude_unset=True)
        if not values:
            return
        _ = await self.session.execute(
            update(AuditRequest)
            .where(col(AuditRequest.id) == audit_request_id)
            .values(**values)
        )
        await self.session.commit()

    async def add_log(self, audit_request_id: uuid.UUID, entry: LogEntry) -> None:
        """Appends the entry in the database (`logs || [entry]`) without loading the row."""
        new_entry = [entry.model_dump(mode="json", exclude_none=True)]
        _ = await self.session.execute(
            update(AuditRequest)
            .where(col(AuditRequest.id) == audit_request_id)
            .values(logs=col(AuditRequest.logs).op("||")(literal(new_entry, JSONB)))
        )
        await self.session.commit()
