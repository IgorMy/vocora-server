from typing import Literal

EXTENSION_FORMAT = Literal[".mp3", ".m4a"]
MAX_AUDIO_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
DIRECTION = Literal["incoming", "outgoing", "call"]
STATUS = Literal["pending", "transcribing", "embedding", "done", "failed"]
SPEAKER = Literal["uplink", "downlink"]
