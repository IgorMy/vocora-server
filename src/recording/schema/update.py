import datetime
import uuid

from pydantic import BaseModel, Field, JsonValue

from src.recording.constants import EXTENSION_FORMAT, STATUS


class RecordingUpdate(BaseModel):
    """
    Fields that can change after a recording is created. The call identity
    (folder, date, contact, direction) is fixed and left out on purpose.
    """

    audio_format: EXTENSION_FORMAT | None = Field(default=None)
    mixed_sha256: str | None = Field(default=None)
    uplink_sha256: str | None = Field(default=None)
    downlink_sha256: str | None = Field(default=None)
    duration_seconds: float | None = Field(default=None)
    version: int | None = Field(default=None)

    status: STATUS | None = Field(default=None)
    attempts: int | None = Field(default=None)
    error: str | None = Field(default=None)
    process_log: list[dict[str, JsonValue]] | None = Field(default=None)
    processed_at: datetime.datetime | None = Field(default=None)

    transcription: str | None = Field(default=None)
    language: str | None = Field(default=None)

    audit_request_id: uuid.UUID | None = Field(default=None)
