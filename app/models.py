from enum import Enum

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    email = "email"
    sms = "sms"
    push = "push"


class RequestStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    sent = "sent"
    failed = "failed"


class RequestCreate(BaseModel):
    to: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    type: NotificationType


class RequestResponse(BaseModel):
    id: str


class RequestStatusResponse(BaseModel):
    id: str
    status: RequestStatus


class RequestItem(BaseModel):
    id: str
    status: RequestStatus
    to: str
    message: str
    type: NotificationType