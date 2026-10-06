import uuid

from fastapi.encoders import jsonable_encoder
from pydantic import JsonValue
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.shared.audit_change.constants import ACTOR
from src.shared.audit_change.model import AuditChange, AuditedTable


class BaseRepository[T: AuditedTable]:
    """
    Base for repositories of audited tables: every create and update writes an
    AuditChange row in the same transaction as the change itself.
    """

    # Columns that change on every write and would only add noise
    ignored_columns: frozenset[str] = frozenset({"updated_at"})

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session: AsyncSession = session
        self.model: type[T] = model
        self.table_name: str = model.__table__.name  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    async def _create(self, record: T, *, actor: ACTOR) -> T:
        changes: dict[str, JsonValue] = record.model_dump(
            mode="json", exclude=set(self.ignored_columns)
        )
        self.session.add(record)
        self.session.add(
            AuditChange(
                table_name=self.table_name,
                record_id=record.id,
                operation="insert",
                changes=changes,
                actor=actor,
            )
        )
        await self.session.commit()
        return record

    async def _update(
        self, record_id: uuid.UUID, values: dict[str, object], *, actor: ACTOR
    ) -> None:
        """Updates the given columns and records the ones whose value changed."""
        if not values:
            return
        # Lock the row so the old values can't change before the update
        old = await self.session.get(self.model, record_id, with_for_update=True)
        if old is None:
            return

        changes: dict[str, JsonValue] = {
            column: {
                "old": jsonable_encoder(getattr(old, column)),
                "new": jsonable_encoder(value),
            }
            for column, value in values.items()
            if column not in self.ignored_columns and getattr(old, column) != value
        }

        _ = await self.session.execute(
            update(self.model).where(col(self.model.id) == record_id).values(**values)
        )
        if changes:
            self.session.add(
                AuditChange(
                    table_name=self.table_name,
                    record_id=record_id,
                    operation="update",
                    changes=changes,
                    actor=actor,
                )
            )
        await self.session.commit()
