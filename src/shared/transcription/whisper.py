# faster-whisper ships without type information
# pyright: reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
import ctypes
import gc
from collections.abc import Mapping
from pathlib import Path

from faster_whisper import WhisperModel, decode_audio

from src.shared.config import settings
from src.shared.transcription.schema import TranscribedSegment, Transcription


def transcribe_files[K](
    language_source: Path, files: Mapping[K, Path]
) -> tuple[str, dict[K, Transcription]]:
    """
    Detects the language on `language_source` and transcribes every file with it.
    Blocking and CPU heavy: call it with asyncio.to_thread.

    The model (~3.5 GB) is loaded here and released before returning, so the
    worker only holds that memory while it is transcribing.
    """
    model = WhisperModel(
        str(settings.whisper_model_path),
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        cpu_threads=settings.whisper_cpu_threads,
    )
    try:
        language = _detect_language(model, language_source)
        return language, {
            key: _transcribe(model, path, language) for key, path in files.items()
        }
    finally:
        del model
        _ = gc.collect()
        # glibc keeps freed memory in its own pools instead of returning it to
        # the system; malloc_trim hands it back so the process really shrinks
        try:
            ctypes.CDLL("libc.so.6").malloc_trim(0)
        except OSError:
            pass


def _detect_language(model: WhisperModel, audio: Path) -> str:
    """Looks at up to 3 chunks of 30 s of speech instead of only the first one."""
    samples = decode_audio(str(audio))
    # decode_audio only returns a tuple of channels with split_stereo=True
    assert not isinstance(samples, tuple)
    language, _, _ = model.detect_language(
        samples, vad_filter=True, language_detection_segments=3
    )
    return language


def _transcribe(model: WhisperModel, audio: Path, language: str) -> Transcription:
    """vad_filter skips the silences, which in a single call channel is about half the audio."""
    segments, info = model.transcribe(str(audio), vad_filter=True, language=language)
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
