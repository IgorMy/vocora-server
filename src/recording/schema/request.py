import datetime
from typing import Annotated, get_args

from fastapi import Form, UploadFile
from fastapi.params import File
from pydantic import BaseModel, field_validator

from src.recording.constants import (
    DIRECTION,
    EXTENSION_FORMAT,
    MAX_AUDIO_FILE_SIZE,
)


class UploadRecordingRequest(BaseModel):
    mixed: Annotated[UploadFile, File()]
    uplink: Annotated[UploadFile, File()]
    downlink: Annotated[UploadFile, File()]
    contact: Annotated[str, Form()]
    date: Annotated[datetime.datetime, Form()]
    direction: Annotated[DIRECTION, Form()]

    @field_validator("mixed")
    @classmethod
    def validate_audio_extension(cls, value: UploadFile) -> UploadFile:
        filename = (value.filename or "").lower()
        if not filename.endswith(get_args(EXTENSION_FORMAT)):
            raise ValueError(
                f"mixed: Invalid file extension. Allowed extensions: {get_args(EXTENSION_FORMAT)}"
            )
        if value.size is not None and value.size > MAX_AUDIO_FILE_SIZE:
            raise ValueError(
                f"mixed: File is too large. Maximum size is {MAX_AUDIO_FILE_SIZE // (1024 * 1024)} MB"
            )
        return value

    @field_validator("uplink")
    @classmethod
    def validate_uplink_extension(cls, value: UploadFile) -> UploadFile:
        filename = (value.filename or "").lower()
        if not filename.endswith(get_args(EXTENSION_FORMAT)):
            raise ValueError(
                f"uplink: Invalid file extension. Allowed extensions: {get_args(EXTENSION_FORMAT)}"
            )
        if value.size is not None and value.size > MAX_AUDIO_FILE_SIZE:
            raise ValueError(
                f"uplink: File is too large. Maximum size is {MAX_AUDIO_FILE_SIZE // (1024 * 1024)} MB"
            )
        return value

    @field_validator("downlink")
    @classmethod
    def validate_downlink_extension(cls, value: UploadFile) -> UploadFile:
        filename = (value.filename or "").lower()
        if not filename.endswith(get_args(EXTENSION_FORMAT)):
            raise ValueError(
                f"downlink: Invalid file extension. Allowed extensions: {get_args(EXTENSION_FORMAT)}"
            )
        if value.size is not None and value.size > MAX_AUDIO_FILE_SIZE:
            raise ValueError(
                f"downlink: File is too large. Maximum size is {MAX_AUDIO_FILE_SIZE // (1024 * 1024)} MB"
            )
        return value
