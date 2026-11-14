"""Общие операции со звонками: сегменты, карточка, заявка, анализ."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_module.core.schemas import TicketAIResult
from backend.api.serializers import call_detail
from backend.models import Call, CallTranscriptSegment, ChatMessage, ChatSession, Ticket
from backend.schemas.call_schemas import CallDetail, TranscriptSegmentRead
from backend.services.accounts import get_or_create_requester
from backend.services.ai_service import analyze_ticket


async def find_call_by_external_id(
    session: AsyncSession, external_id: str
) -> Call | None:
    return await session.scalar(
        select(Call)
        .where(Call.external_id == external_id)
        .order_by(Call.id.desc())
        .limit(1)
    )


async def load_segments(
    session: AsyncSession, call_id: int
) -> list[TranscriptSegmentRead]:
    rows = (
        await session.scalars(
            select(CallTranscriptSegment)
            .where(CallTranscriptSegment.call_id == call_id)
            .order_by(
                CallTranscriptSegment.position, CallTranscriptSegment.id
            )
        )
    ).all()

    return [
        TranscriptSegmentRead(
            id=row.id,
            position=row.position,
            start_ms=row.start_ms,
            end_ms=row.end_ms,
            speaker=row.speaker,
            text=row.text,
            confidence=row.confidence,
        )
        for row in rows
    ]


async def build_call_detail(
    session: AsyncSession, call: Call
) -> CallDetail:
    return call_detail(call, await load_segments(session, call.id))


async def ensure_ticket_for_call(
    session: AsyncSession, call: Call
) -> Ticket:
    """Возвращает заявку звонка, создавая черновик при необходимости."""

    if call.ticket_id is not None:
        ticket = await session.get(Ticket, call.ticket_id)
        if ticket is not None:
            return ticket

    requester = await get_or_create_requester(session)

    text = (
        call.transcript_text
        or "Обращение по телефону (звонок без расшифровки)"
    ).strip()

    chat_session = ChatSession(user_id=requester.id, status="active")
    session.add(chat_session)
    await session.flush()

    session.add(
        ChatMessage(
            session_id=chat_session.id,
            role="user",
            content=text,
        )
    )

    ticket = Ticket(
        chat_session_id=chat_session.id,
        created_by=requester.id,
        raw_text=text,
        channel="voice",
        status="new",
    )
    session.add(ticket)
    await session.flush()

    call.ticket_id = ticket.id
    await session.commit()
    await session.refresh(call)
    await session.refresh(ticket)
    return ticket


async def analyze_call_record(
    session: AsyncSession, call: Call
) -> TicketAIResult:
    """Создаёт/обновляет заявку по звонку и запускает ИИ."""

    ticket = await ensure_ticket_for_call(session, call)
    return await analyze_ticket(
        session, ticket, force=True, call_id=call.id
    )
