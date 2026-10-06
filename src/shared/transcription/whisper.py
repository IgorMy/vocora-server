# faster-whisper ships without type information
# pyright: reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
from functools import cache
from pathlib import Path

from faster_whisper import WhisperModel, decode_audio

from src.shared.config import settings
from src.shared.transcription.schema import TranscribedSegment, Transcription


@cache
def _model() -> WhisperModel:
    # Loaded once per process: it takes seconds and ~2 GB of memory
    return WhisperModel(
        str(settings.whisper_model_path),
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        cpu_threads=settings.whisper_cpu_threads,
    )


def detect_language(audio: Path) -> str:
    """
    Detects the spoken language. Blocking: call it with asyncio.to_thread.
    Looks at up to 3 chunks of 30 s of speech instead of only the first one.
    """
    samples = decode_audio(str(audio))
    # decode_audio only returns a tuple of channels with split_stereo=True
    assert not isinstance(samples, tuple)
    language, _, _ = _model().detect_language(
        samples, vad_filter=True, language_detection_segments=3
    )
    return language


def transcribe(audio: Path, language: str | None = None) -> Transcription:
    """
    Transcribes an audio file. Blocking and CPU heavy: call it with asyncio.to_thread.
    vad_filter skips the silences, which in a single call channel is about half the audio.
    Without `language` it is detected from the audio itself.
    """
    segments, info = _model().transcribe(str(audio), vad_filter=True, language=language)
    return Transcription(
        language=info.language,
        language_probability=info.language_probability,
        duration_seconds=info.duration,
        # segments is a lazy generator: the transcription actually runs here
        segments=[
            TranscribedSegment(start=s.start, end=s.end, text=s.text.strip())
            for s in segments
        ],
    )
