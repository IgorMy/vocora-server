from fastapi import Response

from src.recording.schema.request import UploadRecordingRequest
from src.shared.config import settings


async def upload_recording_service(
    request: UploadRecordingRequest,
) -> Response:

    folder_name = f"{request.date.isoformat()}-{request.contact}-{request.direction}"

    folder = settings.recordings_dir / folder_name

    files = {
        "mixed": folder / "mixed.wav",
        "uplink": folder / "uplink.wav",
        "downlink": folder / "downlink.wav",
    }

    content = {
        "mixed": await request.mixed.read(),
        "uplink": await request.uplink.read(),
        "downlink": await request.downlink.read(),
    }

    # Check if the folder and files already exist and if the content is the same
    if (
        folder.exists()
        and all(file.exists() for file in files.values())
        and all(file.read_bytes() == content[file.stem] for file in files.values())
    ):
        return Response(status_code=200)

    # Write or overwrite the files to the folder
    folder.mkdir(exist_ok=True)
    for name, file in files.items():
        _ = file.write_bytes(content[name])

    return Response(status_code=201)
