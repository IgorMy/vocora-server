import datetime
import uuid

from pydantic import JsonValue
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from src.recording.constants import DIRECTION, EXTENSION_FORMAT, STATUS
from src.shared.audit_change.model import AuditedTable


class Recording(AuditedTable, table=True):
    # Identity of the call; folder is where its audio files live in recordings_dir
    folder: str = Field(unique=True)
    date: datetime.datetime = Field(sa_type=DateTime(timezone=True), index=True)
    contact: str = Field(index=True)
    direction: DIRECTION = Field(sa_type=String)

    # Audio files. The hashes tell whether a re-upload brings new content
    # without reading the stored files from disk.
    audio_format: EXTENSION_FORMAT = Field(sa_type=String)
    mixed_sha256: str = Field()
    uplink_sha256: str = Field()
    downlink_sha256: str = Field()
    duration_seconds: float | None = Field(default=None)
    # Starts at 1 and goes up every time the recording is overwritten with new content
    version: int = Field(default=1)

    # Processing pipeline
    status: STATUS = Field(default="pending", sa_type=String, index=True)
    attempts: int = Field(default=0)
    error: str | None = Field(default=None, sa_type=Text)
    process_log: list[dict[str, JsonValue]] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )
    processed_at: datetime.datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True)
    )

    # Result
    transcription: str | None = Field(default=None, sa_type=Text)
    # Both channels merged by time: [{"speaker", "start", "end", "text"}]
    segments: list[dict[str, JsonValue]] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    language: str | None = Field(default=None)

    # Audit of the upload that created or last overwrote the recording
    audit_request_id: uuid.UUID | None = Field(
        default=None, foreign_key="audit_request.id", ondelete="SET NULL"
    )

    # Soft delete: hidden from the API but kept, together with its audio files
    deleted_at: datetime.datetime | None = Field(
        default=None, sa_type=DateTime(timezone=True), index=True
    )

    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC),
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": lambda: datetime.datetime.now(tz=datetime.UTC)},
    )
