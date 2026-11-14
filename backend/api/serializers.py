"""Преобразование ORM-моделей в ответы API."""

from backend.models import Call, Ticket, TicketAttachment, TicketMessage, User
from backend.schemas.call_schemas import CallDetail, CallRead
from backend.schemas.ticket_schemas import (
    AttachmentRead,
    CallSummary,
    MessageRead,
    TicketDetail,
    TicketSummary,
    UserRead,
)


def user_read(user: User | None) -> UserRead | None:
    if user is None:
        return None
    return UserRead(
        id=user.id,
        name=user.name,
        role=user.role,
        specialty=user.specialty,
        phone=user.phone,
    )


def attachment_read(attachment: TicketAttachment) -> AttachmentRead:
    return AttachmentRead(
        id=attachment.id,
        ticket_id=attachment.ticket_id,
        message_id=attachment.message_id,
        kind=attachment.kind,
        filename=attachment.filename,
        mime_type=attachment.mime_type,
        size_bytes=attachment.size_bytes,
        sha256=attachment.sha256,
        description=attachment.description,
        url=f"/api/attachments/{attachment.id}/content",
        created_at=attachment.created_at,
    )


def message_read(
    message: TicketMessage,
    attachments: list[AttachmentRead] | None = None,
) -> MessageRead:
    return MessageRead(
        id=message.id,
        ticket_id=message.ticket_id,
        role=message.role,
        text=message.text,
        created_at=message.created_at,
        attachments=attachments or [],
    )


def call_summary(call: Call) -> CallSummary:
    preview = None
    if call.transcript_text:
        preview = call.transcript_text.strip()[:160]
    return CallSummary(
        id=call.id,
        ticket_id=call.ticket_id,
        external_id=call.external_id,
        direction=call.direction,
        transport=call.transport,
        provider=call.provider,
        client_phone=call.client_phone,
        status=call.status,
        started_at=call.started_at,
        ended_at=call.ended_at,
        duration_seconds=call.duration_seconds,
        has_recording=call.recording_size is not None,
        recording_url=(
            f"/api/calls/{call.id}/recording"
            if call.recording_size is not None
            else None
        ),
        transcript_preview=preview,
    )


def call_read(call: Call) -> CallRead:
    return CallRead(
        id=call.id,
        ticket_id=call.ticket_id,
        external_id=call.external_id,
        direction=call.direction,
        transport=call.transport,
        provider=call.provider,
        client_phone=call.client_phone,
        status=call.status,
        started_at=call.started_at,
        ended_at=call.ended_at,
        duration_seconds=call.duration_seconds,
        recording_mime=call.recording_mime,
        recording_size=call.recording_size,
        has_recording=call.recording_size is not None,
        recording_url=(
            f"/api/calls/{call.id}/recording"
            if call.recording_size is not None
            else None
        ),
        transcript_text=call.transcript_text,
        transcript_language=call.transcript_language,
        transcript_provider=call.transcript_provider,
        created_at=call.created_at,
    )


def call_detail(call: Call, segments: list) -> CallDetail:
    base = call_read(call)
    return CallDetail(
        **base.model_dump(),
        segments=segments,
    )


def ticket_summary(ticket: Ticket, assignee: User | None) -> TicketSummary:
    return TicketSummary(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        source=ticket.source,
        status=ticket.status,
        priority=ticket.priority,
        category_code=ticket.category_code,
        subcategory_code=ticket.subcategory_code,
        client_name=ticket.client_name,
        client_phone=ticket.client_phone,
        assignee=user_read(assignee),
        ai_description=ticket.ai_description,
        ai_solution=ticket.ai_solution,
        ai_confidence=ticket.ai_confidence,
        needs_human_review=ticket.needs_human_review,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def ticket_detail(
    ticket: Ticket,
    assignee: User | None,
    messages: list[MessageRead],
    attachments: list[AttachmentRead],
    calls: list[CallSummary],
) -> TicketDetail:
    return TicketDetail(
        **ticket_summary(ticket, assignee).model_dump(),
        messages=messages,
        attachments=attachments,
        calls=calls,
    )
