from pathlib import Path
from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", extra="ignore"
    )
    recordings_dir: Path = Path("data/recordings")
    api_token: SecretStr

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Transcription (faster-whisper). The model is downloaded with `make download_model`
    # into whisper_model_dir/<whisper_model>.
    whisper_model: str = "large-v3"
    whisper_model_dir: Path = Path("data/models")
    whisper_device: str = "cpu"  # "cpu" or "cuda"
    whisper_compute_type: str = "int8"  # "int8" on CPU, "float16" on GPU
    whisper_cpu_threads: int = 4

    @property
    def whisper_model_path(self) -> Path:
        return self.whisper_model_dir / self.whisper_model

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


settings: Settings = Settings()  # pyright: ignore[reportCallIssue]
