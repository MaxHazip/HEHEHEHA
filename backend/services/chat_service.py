"""Чат заявки: сообщение пользователя + ответ LLM (обычный и streaming)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from ai_module.core.analyzer import get_analyzer
from ai_module.core.chat import generate_reply, generate_reply_stream
from ai_module.core.schemas import TicketAIResult
from backend.models import ChatMessage, Ticket, TicketAttachment
from backend.schemas.chat_schemas import ChatRequest
from backend.services.ai_service import (
    analysis_result,
    analyze_ticket,
    latest_analysis,
)

logger = logging.getLogger(__name__)


@dataclass
class PreparedChat:
    ticket_id: int
    history: list[dict[str, str]]
    context: str
    fallback: str


async def _context(
    session: AsyncSession, ticket: Ticket
) -> str:
    analysis = await latest_analysis(session, ticket)
    result = analysis_result(analysis)
    lines: list[str] = []

    if result is not None:
        lines.append(
            "Категория: "
            f"{result.classification.category_code}/"
            f"{result.classification.subcategory_code}"
        )
        if result.issue.description:
            lines.append(f"Проблема: {result.issue.description}")
        if result.issue.symptoms:
            lines.append(
                "Симптомы: " + ", ".join(result.issue.symptoms)
            )
        if result.intake.missing_fields:
            lines.append(
                "Не хватает: " + ", ".join(result.intake.missing_fields)
            )
        if result.intake.questions_to_client:
            lines.append(
                "Уже спрашивали: "
                + "; ".join(
                    item.question
                    for item in result.intake.questions_to_client
                )
            )
    else:
        lines.append(f"Начальный текст: {ticket.raw_text[:500]}")

    if ticket.room:
        lines.append(f"Кабинет: {ticket.room}")
    if ticket.building:
        lines.append(f"Здание: {ticket.building}")
    if ticket.device:
        lines.append(f"Устройство: {ticket.device}")

    return "\n".join(lines)


def _fallback_reply(result: TicketAIResult | None) -> str:
    if result is not None and result.intake.questions_to_client:
        return result.intake.questions_to_client[0].question
    return (
        "Опишите, пожалуйста, подробнее: что именно не работает, "
        "в каком кабинете и что вы уже пробовали сделать?"
    )


async def _store_user_message(
    session: AsyncSession,
    ticket: Ticket,
    payload: ChatRequest,
) -> None:
    text = payload.text.strip()
    if not text and not payload.attachment_ids:
        raise ValueError("Сообщение пустое")

    message = ChatMessage(
        session_id=ticket.chat_session_id,
        role="user",
        content=text or "[вложение]",
    )
    session.add(message)
    await session.flush()

    if payload.attachment_ids:
        rows = (
            await session.scalars(
                select(TicketAttachment)
                .options(defer(TicketAttachment.data))
                .where(
                    TicketAttachment.id.in_(payload.attachment_ids),
                    TicketAttachment.ticket_id == ticket.id,
                )
            )
        ).all()
        found = {row.id for row in rows}
        missing = set(payload.attachment_ids) - found
        if missing:
            raise ValueError(
                f"Вложения не найдены: {sorted(missing)}"
            )
        for row in rows:
            row.message_id = message.id
            row.ticket_id = ticket.id

    await session.commit()


async def prepare_chat(
    session: AsyncSession,
    ticket: Ticket,
    payload: ChatRequest,
) -> PreparedChat:
    """Сохраняет сообщение, обновляет заявку и готовит контекст ответа."""

    await _store_user_message(session, ticket, payload)

    # Сначала rule-based анализ (и vision для фото), чтобы ответ модели
    # уже знал категорию, кабинет, здание и недостающие поля.
    try:
        await analyze_ticket(
            session, ticket, force=True, use_llm=False
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Не удалось обновить заявку перед ответом чата"
        )

    result = analysis_result(await latest_analysis(session, ticket))

    history_rows = (
        await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == ticket.chat_session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        )
    ).all()
    history = [
        {"role": item.role, "content": item.content}
        for item in history_rows[-20:]
    ]

    return PreparedChat(
        ticket_id=ticket.id,
        history=history,
        context=await _context(session, ticket),
        fallback=_fallback_reply(result),
    )


async def finish_chat(
    session: AsyncSession,
    ticket: Ticket,
    reply: str,
) -> None:
    session.add(
        ChatMessage(
            session_id=ticket.chat_session_id,
            role="assistant",
            content=reply,
        )
    )
    await session.commit()


async def send_chat_message(
    session: AsyncSession,
    ticket: Ticket,
    payload: ChatRequest,
) -> str:
    prepared = await prepare_chat(session, ticket, payload)

    reply = await generate_reply(
        get_analyzer().provider,
        prepared.history,
        context=prepared.context,
    )
    if not reply:
        reply = prepared.fallback

    await finish_chat(session, ticket, reply)
    return reply


async def generate_chat_deltas(
    prepared: PreparedChat,
) -> AsyncIterator[str]:
    async for delta in generate_reply_stream(
        get_analyzer().provider,
        prepared.history,
        context=prepared.context,
    ):
        yield delta
