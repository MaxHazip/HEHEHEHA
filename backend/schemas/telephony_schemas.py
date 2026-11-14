from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SipCallStart(BaseModel):
    """Событие начала звонка от SIP-АТС."""

    external_id: str = Field(min_length=1, max_length=128)
    direction: Literal["inbound", "outbound"] = "inbound"
    from_number: str | None = None
    to_number: str | None = None
    client_phone: str | None = None
    provider: str = "asterisk"
    started_at: datetime | None = None


class SipCallEnd(BaseModel):
    """Событие завершения звонка."""

    status: Literal["completed", "missed", "failed"] = "completed"
    duration_seconds: int | None = Field(default=None, ge=0)
    recording_url: str | None = None
    recording_mime: str | None = None
