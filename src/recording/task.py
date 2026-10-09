import asyncio
import datetime
import uuid
from pathlib import Path

from procrastinate import RetryStrategy
from pydantic import JsonValue

from src.recording.constants import SPEAKER
from src.recording.repository import RecordingRepository
from src.recording.schema.segment import RecordingSegment
from src.recording.schema.update import RecordingUpdate
from src.shared.audit_request.model import LogEntry
from src.shared.config import settings
from src.shared.database.engine import get_session_factory
from src.shared.queue.app import queue_app
from src.shared.transcription.whisper import transcribe_files


@queue_app.task(
    name="process_recording",
    queue="recording",
    retry=RetryStrategy(max_attempts=3, exponential_wait=10),
)
async def process_recording(recording_id: str, version: int) -> None:
    async with get_session_factory()() as session:
        repository = RecordingRepository(session)
        recording = await repository.get(uuid.UUID(recording_id))

        # Overwritten after this job was queued (the job for the new version will
        # process it) or deleted: nothing to do
        if (
            recording is None
            or recording.version != version
            or recording.deleted_at is not None
        ):
            return

        process_log: list[dict[str, JsonValue]] = [
            *recording.process_log,
            LogEntry(
                timestamp=datetime.datetime.now(tz=datetime.UTC),
                level="INFO",
                event="Processing started",
                extra={"version": version},
            ).model_dump(mode="json", exclude_none=True),
        ]
        await repository.update(
            recording.id,
            RecordingUpdate(
                status="transcribing",
                attempts=recording.attempts + 1,
                error=None,
                process_log=process_log,
            ),
            actor="system",
        )

        try:
            # Each side of the call has its own channel, so who said what comes
            # for free: transcribe both and merge their segments by time.
            # Whisper is blocking, it runs in a thread to keep the worker loop free.
            folder = settings.recordings_dir / recording.folder
            # The language is detected once on the mixed audio, which has both voices,
            # and forced on each channel: a channel with little speech (someone who
            # mostly listens) can't be trusted to detect it and gets transcribed as
            # gibberish in another language.
            channels: dict[SPEAKER, Path] = {
                "uplink": folder / f"uplink{recording.audio_format}",
                "downlink": folder / f"downlink{recording.audio_format}",
            }
            language, transcriptions = await asyncio.to_thread(
                transcribe_files, folder / f"mixed{recording.audio_format}", channels
            )
            segments = sorted(
                (
                    RecordingSegment(
                        speaker=speaker, start=s.start, end=s.end, text=s.text
                    )
                    for speaker, transcription in transcriptions.items()
                    for s in transcription.segments
                ),
                key=lambda segment: segment.start,
            )
            duration_seconds = max(t.duration_seconds for t in transcriptions.values())
            # Readable dialogue: "[01:05] Ana: ..." (uplink is the phone owner)
            dialogue = "\n".join(
                f"[{int(segment.start) // 60:02d}:{int(segment.start) % 60:02d}] "
                + f"{'Yo' if segment.speaker == 'uplink' else recording.contact}: "
                + segment.text
                for segment in segments
            )
        except Exception as exc:
            process_log.append(
                LogEntry(
                    timestamp=datetime.datetime.now(tz=datetime.UTC),
                    level="ERROR",
                    event="Processing failed",
                    extra={"error": str(exc)},
                ).model_dump(mode="json", exclude_none=True)
            )
            await repository.update(
                recording.id,
                RecordingUpdate(
                    status="failed", error=str(exc), process_log=process_log
                ),
                actor="system",
            )
            # Re-raised so procrastinate retries the job
            raise

        process_log.append(
            LogEntry(
                timestamp=datetime.datetime.now(tz=datetime.UTC),
                level="INFO",
                event="Processing finished",
                extra={
                    "language": language,
                    "duration_seconds": duration_seconds,
                    "segments": len(segments),
                },
            ).model_dump(mode="json", exclude_none=True)
        )
        await repository.update(
            recording.id,
            RecordingUpdate(
                status="done",
                transcription=dialogue,
                segments=[segment.model_dump() for segment in segments],
                language=language,
                duration_seconds=duration_seconds,
                processed_at=datetime.datetime.now(tz=datetime.UTC),
                process_log=process_log,
            ),
            actor="system",
        )
