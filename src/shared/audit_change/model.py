import datetime
import uuid

from pydantic import JsonValue
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from src.shared.audit_change.constants import ACTOR, OPERATION
from src.shared.database.table import TableModel


class AuditChange(TableModel, table=True):
    """One row per change in an audited table, written by BaseRepository."""

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC),
        sa_type=DateTime(timezone=True),
        index=True,
    )
    table_name: str = Field(index=True)
    record_id: uuid.UUID = Field(index=True)
    operation: OPERATION = Field(sa_type=String)
    # insert: the whole row; update: {"column": {"old": ..., "new": ...}}
    changes: dict[str, JsonValue] = Field(sa_column=Column(JSONB, nullable=False))
    actor: ACTOR = Field(sa_type=String)


class AuditedTable(TableModel):
    """
    Base for table models whose changes are audited through BaseRepository.
    It provides the uuid primary key the audit rows point to.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
