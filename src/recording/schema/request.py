import datetime
from typing import Annotated, Literal

from fastapi import Form, UploadFile
from pydantic import BaseModel


class UploadRecordingRequest(BaseModel):
    mixed: UploadFile
    uplink: UploadFile
    downlink: UploadFile
    contact: Annotated[str, Form()]
    date: Annotated[datetime.datetime, Form()]
    direction: Annotated[Literal["incoming", "outgoing", "call"], Form()]
