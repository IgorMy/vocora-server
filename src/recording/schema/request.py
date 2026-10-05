import datetime
from typing import Annotated, Literal

from fastapi import Form, UploadFile
from fastapi.params import File
from pydantic import BaseModel


class UploadRecordingRequest(BaseModel):
    mixed: Annotated[UploadFile, File()]
    uplink: Annotated[UploadFile, File()]
    downlink: Annotated[UploadFile, File()]
    contact: Annotated[str, Form()]
    date: Annotated[datetime.datetime, Form()]
    direction: Annotated[Literal["incoming", "outgoing", "call"], Form()]
