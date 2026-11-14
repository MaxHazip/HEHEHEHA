from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.knowledge_schemas import KnowledgeArticleRead

TicketSource = Literal["chat", "web", "phone"]
TicketStatus = Literal["draft", "new", "in_progress", "resolved", "closed"]
TicketPriority = Literal["low", "medium", "high", "critical"]
MessageRole = Literal[
    "user", "assistant", "client", "bot", "dispatcher", "engineer"
]


def normalize_role(role: str) -> str:
    """Приводит роли клиента/бота к схеме chat_messages."""

    if role in ("assistant", "bot", "dispatcher", "engineer"):
        return "assistant"
    return "user"


class UserRead(BaseModel):
    id: int
    name: str
    role: str
    email: str
    # Первая компетенция инженера — для обратной совместимости UI.
    specialty: str | None = None
    # id профиля Engineer (нужен для POST /api/tickets/{id}/assign).
    engineer_id: int | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AttachmentRead(BaseModel):
    id: int
    ticket_id: int | None = None
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
    ticket_id: int | None = None
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
    priority: TicketPriority | None = None
    client_name: str | None = None
    client_phone: str | None = None
    # None — решает AI_AUTO_ANALYZE; false — не анализировать при
    # создании (клиент вызовет /analyze сам, с файлами и сообщением).
    auto_analyze: bool | None = None


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category_id: int | None = None
    subcategory_id: int | None = None
    engineer_id: int | None = None
    needs_human_review: bool | None = None
    is_mass_incident: bool | None = None
    device: str | None = None
    building: str | None = None
    floor: str | None = None
    room: str | None = None
    host: str | None = None
    ai_description: str | None = None


class TicketAssign(BaseModel):
    engineer_id: int


class MessageCreate(BaseModel):
    role: MessageRole = "user"
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
    knowledge: list[KnowledgeArticleRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TicketDetail(TicketSummary):
    messages: list[MessageRead] = Field(default_factory=list)
    attachments: list[AttachmentRead] = Field(default_factory=list)
    calls: list[CallSummary] = Field(default_factory=list)
