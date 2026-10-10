from pydantic import BaseModel, Field


class TranscribedWord(BaseModel):
    start: float = Field()
    end: float = Field()
    # As Whisper returns it, with its leading space (" hola"): joining words
    # back with "".join keeps the original spacing and punctuation
    text: str = Field()


class TranscribedSegment(BaseModel):
    start: float = Field()
    end: float = Field()
    text: str = Field()
    words: list[TranscribedWord] = Field()


class Transcription(BaseModel):
    language: str = Field()
    language_probability: float = Field()
    duration_seconds: float = Field()
    segments: list[TranscribedSegment] = Field()
