import datetime
import uuid
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from src.recording.constants import DIRECTION, STATUS
from src.recording.schema.segment import RecordingSegment


class RecordingSummary(BaseModel):
    """What the list returns for each recording: everything but the heavy content."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field()
    date: datetime.datetime = Field()
    contact: str = Field()
    direction: DIRECTION = Field()
    status: STATUS = Field()
    duration_seconds: float | None = Field()
    language: str | None = Field()
    version: int = Field()
    created_at: datetime.datetime = Field()
    updated_at: datetime.datetime = Field()
    # Set when the recording was deleted (only listed with deleted=include/only)
    deleted_at: datetime.datetime | None = Field()


class RecordingDetail(RecordingSummary):
    audio_format: str = Field()
    transcription: str | None = Field()
    segments: list[RecordingSegment] | None = Field()
    processed_at: datetime.datetime | None = Field()
    error: str | None = Field()


class RecordingPage(BaseModel):
    items: list[RecordingSummary] = Field()
    # Offset of the next page, or None when this one is the last
    next_offset: int | None = Field()
