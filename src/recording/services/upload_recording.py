import hashlib

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.recording.model import Recording
from src.recording.repository import RecordingRepository
from src.recording.schema.request import UploadRecordingRequest
from src.recording.schema.update import RecordingUpdate
from src.recording.task import process_recording
from src.shared.audit_request.log import audit_log, current_audit_request_id
from src.shared.config import settings


async def upload_recording_service(
    request: UploadRecordingRequest,
    session: AsyncSession,
) -> Response:

    folder_name = f"{request.date.isoformat()}-{request.contact}-{request.direction}"

    folder = settings.recordings_dir / folder_name

    files = {
        "mixed": folder / f"mixed.{request.mixed.filename.split('.')[-1].lower()}",  # pyright: ignore[reportOptionalMemberAccess]
        "uplink": folder / f"uplink.{request.uplink.filename.split('.')[-1].lower()}",  # pyright: ignore[reportOptionalMemberAccess]
        "downlink": folder
        / f"downlink.{request.downlink.filename.split('.')[-1].lower()}",  # pyright: ignore[reportOptionalMemberAccess]
    }

    content = {
        "mixed": await request.mixed.read(),
        "uplink": await request.uplink.read(),
        "downlink": await request.downlink.read(),
    }

    await audit_log(
        "INFO",
        "Recording received",
        {
            "folder": folder_name,
            "sizes": {name: len(data) for name, data in content.items()},
        },
    )

    # Check if the folder and files already exist and if the content is the same
    if (
        folder.exists()
        and all(file.exists() for file in files.values())
        and all(file.read_bytes() == content[file.stem] for file in files.values())
    ):
        await audit_log("INFO", "Recording already exists with the same content")
        return Response(status_code=200)

    if folder.exists():
        await audit_log("INFO", "Overwriting existing recording with new content")

    # Write or overwrite the files to the folder
    folder.mkdir(exist_ok=True)
    for name, file in files.items():
        _ = file.write_bytes(content[name])

    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in content.items()}
    audio_format = files["mixed"].suffix
    repository = RecordingRepository(session)
    recording = await repository.get_by_folder(folder_name)
    if recording is None:
        recording = await repository.create(
            Recording(
                folder=folder_name,
                date=request.date,
                contact=request.contact,
                direction=request.direction,
                audio_format=audio_format,  # pyright: ignore[reportArgumentType]
                mixed_sha256=hashes["mixed"],
                uplink_sha256=hashes["uplink"],
                downlink_sha256=hashes["downlink"],
                audit_request_id=current_audit_request_id.get(),
            ),
            actor="request",
        )
        version = recording.version
    else:
        # New content for an existing recording: it has to be processed again
        version = recording.version + 1
        await repository.update(
            recording.id,
            RecordingUpdate(
                audio_format=audio_format,  # pyright: ignore[reportArgumentType]
                mixed_sha256=hashes["mixed"],
                uplink_sha256=hashes["uplink"],
                downlink_sha256=hashes["downlink"],
                version=version,
                status="pending",
                audit_request_id=current_audit_request_id.get(),
                # Uploading new content brings a deleted recording back
                deleted_at=None,
            ),
            actor="request",
        )

    await audit_log("INFO", "Recording saved", {"recording_id": str(recording.id)})

    # lock: jobs of the same recording run one after another, never at the same time
    job_id = await process_recording.configure(lock=str(recording.id)).defer_async(
        recording_id=str(recording.id), version=version
    )
    await audit_log("INFO", "Recording queued for processing", {"job_id": job_id})

    return Response(status_code=201)
