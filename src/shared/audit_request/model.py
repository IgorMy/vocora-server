import datetime
import uuid

from pydantic import BaseModel, JsonValue
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from src.shared.audit_request.constants import LOG_LEVEL
from src.shared.database.table import TableModel


class LogEntry(BaseModel):
    timestamp: datetime.datetime
    level: LOG_LEVEL
    event: str
    extra: dict[str, JsonValue] | None = None


class AuditRequest(TableModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC),
        sa_type=DateTime(timezone=True),
        index=True,
    )
    method: str
    path: str = Field(index=True)
    query_params: dict[str, JsonValue] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    status_code: int | None = Field(default=None, index=True)
    duration_ms: int | None = Field(default=None)

    client_ip: str | None = Field(default=None, index=True)
    user_agent: str | None = Field(default=None)

    logs: list[dict[str, JsonValue]] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )

    error: dict[str, JsonValue] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
