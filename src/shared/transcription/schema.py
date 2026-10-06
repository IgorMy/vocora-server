from pydantic import BaseModel, Field


class TranscribedSegment(BaseModel):
    start: float = Field()
    end: float = Field()
    text: str = Field()


class Transcription(BaseModel):
    language: str = Field()
    language_probability: float = Field()
    duration_seconds: float = Field()
    segments: list[TranscribedSegment] = Field()
