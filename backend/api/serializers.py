"""Преобразование ORM-моделей в ответы API."""


from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from ai_module.core.schemas import TicketAIResult
from backend.models import (
    Call,
    Category,
    ChatMessage,
    Engineer,
    Subcategory,
    Ticket,
    TicketAnalysis,
    TicketAttachment,
    User,
)

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

from backend.services.ai_service import (
    analysis_result,
    latest_analysis,
    render_summary,
)

_SOURCE_BY_CHANNEL = {"chat": "chat", "voice": "phone", "image": "chat"}


def user_read(
    user: User | None,
    specialty: str | None = None,
    engineer_id: int | None = None,
) -> UserRead | None:



def user_read(user: User | None) -> UserRead | None:

    if user is None:
        return None
    return UserRead(
        id=user.id,
        name=user.name,
        role=user.role,

        email=user.email,
        specialty=specialty,
        engineer_id=engineer_id,
    )


async def _assignee(
    session: AsyncSession, ticket: Ticket
) -> UserRead | None:
    if ticket.engineer_id is None:
        return None
    engineer = await session.get(Engineer, ticket.engineer_id)
    if engineer is None:
        return None
    user = await session.get(User, engineer.user_id)
    specialty = engineer.competencies[0] if engineer.competencies else None
    return user_read(user, specialty, engineer.id)



        specialty=user.specialty,
        phone=user.phone,
    )



def attachment_read(attachment: TicketAttachment) -> AttachmentRead:
    return AttachmentRead(
        id=attachment.id,
        ticket_id=attachment.ticket_id,
        message_id=attachment.message_id,
        kind=attachment.kind,

        filename=attachment.file_name,
        mime_type=attachment.mime_type,
        size_bytes=attachment.file_size,

        filename=attachment.filename,
        mime_type=attachment.mime_type,
        size_bytes=attachment.size_bytes,

        sha256=attachment.sha256,
        description=attachment.description,
        url=f"/api/attachments/{attachment.id}/content",
        created_at=attachment.created_at,
    )


def message_read(

    message: ChatMessage,
    ticket_id: int | None,

    message: TicketMessage,

    attachments: list[AttachmentRead] | None = None,
) -> MessageRead:
    return MessageRead(
        id=message.id,

        ticket_id=ticket_id,
        role=message.role,
        text=message.content,

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



def _title(
    ticket: Ticket,
    category: Category | None,
    subcategory: Subcategory | None,
) -> str:
    parts: list[str] = []
    if category is not None:
        parts.append(category.name)
    if subcategory is not None:
        parts.append(subcategory.name)

    if parts:
        title = ": ".join(parts)
    else:
        title = " ".join(ticket.raw_text.split())[:80] or "Обращение"

    if ticket.room:
        title = f"{title} — каб. {ticket.room}"
    return title[:120]


async def _ai_fields(
    session: AsyncSession, ticket: Ticket
) -> tuple[TicketAnalysis | None, TicketAIResult | None]:
    analysis = await latest_analysis(session, ticket)
    return analysis, analysis_result(analysis)


async def build_ticket_summary(
    session: AsyncSession, ticket: Ticket
) -> TicketSummary:
    assignee = await _assignee(session, ticket)

    category = (
        await session.get(Category, ticket.category_id)
        if ticket.category_id
        else None
    )
    subcategory = (
        await session.get(Subcategory, ticket.subcategory_id)
        if ticket.subcategory_id
        else None
    )

    analysis, result = await _ai_fields(session, ticket)

    description = ticket.raw_text
    if result is not None and result.issue.description:
        description = result.issue.description

    ai_description = render_summary(result) if result is not None else None
    ai_solution = (
        "\n".join(result.decision_notes)
        if result is not None and result.decision_notes
        else None
    )

    return TicketSummary(
        id=ticket.id,
        title=_title(ticket, category, subcategory),
        description=description,
        source=_SOURCE_BY_CHANNEL.get(ticket.channel, "chat"),
        status=ticket.status,
        priority=ticket.priority or "medium",
        category_code=category.code if category else "none",
        subcategory_code=subcategory.code if subcategory else "none",
        assignee=assignee,
        ai_description=ai_description,
        ai_solution=ai_solution,
        ai_confidence=(
            analysis.confidence
            if analysis is not None
            else (
                result.confidence.overall if result is not None else None
            )
        ),

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



async def build_ticket_detail(
    session: AsyncSession, ticket: Ticket
) -> TicketDetail:
    summary = await build_ticket_summary(session, ticket)

    messages = (
        await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == ticket.chat_session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        )
    ).all()

    attachments = (
        await session.scalars(
            select(TicketAttachment)
            .options(defer(TicketAttachment.data))
            .where(TicketAttachment.ticket_id == ticket.id)
            .order_by(TicketAttachment.id)
        )
    ).all()
    attachment_reads = [attachment_read(item) for item in attachments]

    by_message: dict[int, list[AttachmentRead]] = {}
    for item in attachment_reads:
        if item.message_id is not None:
            by_message.setdefault(item.message_id, []).append(item)

    message_reads = [
        message_read(message, ticket.id, by_message.get(message.id))
        for message in messages
    ]

    calls = (
        await session.scalars(
            select(Call)
            .options(defer(Call.recording_data))
            .where(Call.ticket_id == ticket.id)
            .order_by(Call.id)
        )
    ).all()

    return TicketDetail(
        **summary.model_dump(),
        messages=message_reads,
        attachments=attachment_reads,
        calls=[call_summary(call) for call in calls],

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
