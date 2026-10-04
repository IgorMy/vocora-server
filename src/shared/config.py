from pathlib import Path
from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file=".env")
    recordings_dir: Path = Path("data/recordings")
    api_token: SecretStr


settings: Settings = Settings()  # pyright: ignore[reportCallIssue]
