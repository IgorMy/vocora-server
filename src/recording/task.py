import datetime
import uuid

from procrastinate import RetryStrategy
from pydantic import JsonValue

from src.recording.repository import RecordingRepository
from src.recording.schema.update import RecordingUpdate
from src.shared.audit_request.model import LogEntry
from src.shared.database.engine import get_session_factory
from src.shared.queue.app import queue_app


@queue_app.task(
    name="process_recording",
    queue="recording",
    retry=RetryStrategy(max_attempts=3, exponential_wait=10),
)
async def process_recording(recording_id: str, version: int) -> None:
    async with get_session_factory()() as session:
        repository = RecordingRepository(session)
        recording = await repository.get(uuid.UUID(recording_id))

        # Overwritten after this job was queued: the job for the new version will process it
        if recording is None or recording.version != version:
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
            # Transcription and embedding will run here
            pass
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
            ).model_dump(mode="json", exclude_none=True)
        )
        await repository.update(
            recording.id,
            RecordingUpdate(
                status="done",
                processed_at=datetime.datetime.now(tz=datetime.UTC),
                process_log=process_log,
            ),
            actor="system",
        )
