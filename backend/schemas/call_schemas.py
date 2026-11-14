from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CallDirection = Literal["inbound", "outbound"]
CallTransport = Literal["webrtc", "sip"]
CallStatus = Literal["ringing", "active", "completed", "missed", "failed"]


class CallCreate(BaseModel):
    ticket_id: int | None = None
    direction: CallDirection = "inbound"
    transport: CallTransport = "webrtc"
    provider: str | None = "browser"
    client_phone: str | None = None
    status: CallStatus = "active"


class CallUpdate(BaseModel):
    status: CallStatus | None = None
    ended_at: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0)


class TranscriptSegmentIn(BaseModel):
    start_ms: int | None = Field(default=None, ge=0)
    end_ms: int | None = Field(default=None, ge=0)
    speaker: str | None = None
    text: str = ""
    confidence: float | None = Field(default=None, ge=0, le=1)


class TranscriptUpdate(BaseModel):
    text: str = ""
    language: str = "ru-RU"
    provider: str = "browser-google"
    segments: list[TranscriptSegmentIn] = Field(default_factory=list)


class TranscriptSegmentRead(TranscriptSegmentIn):
    id: int
    position: int


class CallRead(BaseModel):
    id: int
    ticket_id: int | None = None
    external_id: str | None = None
    direction: str
    transport: str
    provider: str | None = None
    client_phone: str | None = None
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    recording_mime: str | None = None
    recording_size: int | None = None
    has_recording: bool = False
    recording_url: str | None = None
    transcript_text: str | None = None
    transcript_language: str | None = None
    transcript_provider: str | None = None
    created_at: datetime


class CallDetail(CallRead):
    segments: list[TranscriptSegmentRead] = Field(default_factory=list)
