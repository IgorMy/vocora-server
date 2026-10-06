from pydantic import BaseModel, Field

from src.recording.constants import SPEAKER


class RecordingSegment(BaseModel):
    """A piece of the call: who said what, and when (seconds from the start)."""

    speaker: SPEAKER = Field()
    start: float = Field()
    end: float = Field()
    text: str = Field()
