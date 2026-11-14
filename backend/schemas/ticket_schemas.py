from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TicketSource = Literal["chat", "web", "phone"]
TicketStatus = Literal["new", "in_progress", "closed", "rejected"]
TicketPriority = Literal["low", "medium", "high", "critical", "needs_review"]
MessageRole = Literal["client", "bot", "dispatcher", "engineer"]


class UserRead(BaseModel):
    id: int
    name: str
    role: str
    specialty: str | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AttachmentRead(BaseModel):
    id: int
    ticket_id: int
    message_id: int | None = None
    kind: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str | None = None
    description: str | None = None
    url: str
    created_at: datetime


class MessageRead(BaseModel):
    id: int
    ticket_id: int
    role: str
    text: str
    created_at: datetime
    attachments: list[AttachmentRead] = Field(default_factory=list)


class CallSummary(BaseModel):
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
    has_recording: bool = False
    recording_url: str | None = None
    transcript_preview: str | None = None


class TicketCreate(BaseModel):
    title: str | None = None
    description: str = ""
    source: TicketSource = "chat"
    priority: TicketPriority = "medium"
    client_name: str | None = None
    client_phone: str | None = None


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category_code: str | None = None
    subcategory_code: str | None = None
    assignee_id: int | None = None
    ai_description: str | None = None
    ai_solution: str | None = None


class TicketAssign(BaseModel):
    assignee_id: int


class MessageCreate(BaseModel):
    role: MessageRole = "client"
    text: str = Field(default="", max_length=20_000)
    attachment_ids: list[int] = Field(default_factory=list)


class TicketSummary(BaseModel):
    id: int
    title: str
    description: str
    source: str
    status: str
    priority: str
    category_code: str
    subcategory_code: str
    client_name: str | None = None
    client_phone: str | None = None
    assignee: UserRead | None = None
    ai_description: str | None = None
    ai_solution: str | None = None
    ai_confidence: float | None = None
    needs_human_review: bool = True
    created_at: datetime
    updated_at: datetime


class TicketDetail(TicketSummary):
    messages: list[MessageRead] = Field(default_factory=list)
    attachments: list[AttachmentRead] = Field(default_factory=list)
    calls: list[CallSummary] = Field(default_factory=list)
