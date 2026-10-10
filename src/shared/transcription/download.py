# faster-whisper ships without type information
# pyright: reportMissingTypeStubs=false, reportUnknownVariableType=false
from faster_whisper.utils import download_model

from src.shared.config import settings

if __name__ == "__main__":
    path = download_model(
        settings.whisper_model, output_dir=str(settings.whisper_model_path)
    )
    print(f"Model {settings.whisper_model} ready at {path}")
