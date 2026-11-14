"""Связка backend-моделей и ИИ-модуля."""

from __future__ import annotations

import logging

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from ai_module.core.analyzer import get_analyzer
from ai_module.core.clarification import FIELD_LABELS
from ai_module.core.schemas import (
    AnalysisRequest,
    Attachment as AIAttachment,
    Message as AIMessage,
    OperatorOverrides,
    TicketAIResult,
)
from ai_module.core.taxonomy import (
    ATTEMPTED_ACTIONS,
    SYMPTOMS,
    TAXONOMY_VERSION,
    category_name,
    get_taxonomy,
    subcategory_by_code,
)
from ai_module.services.image_service import describe_attachment
from backend.models import (
    Call,
    Category,
    ChatMessage,
    Subcategory,
    Ticket,
    TicketAnalysis,
    TicketAttachment,
)
from backend.models.ticket import TICKET_PRIORITIES

logger = logging.getLogger(__name__)

_IMPACT_LABELS = {
    "single_device": "одно устройство",
    "single_user": "один пользователь",
    "department": "отдел",
    "building": "здание",
    "multiple_buildings": "несколько зданий",
    "unknown": "неизвестно",
}

_MASS_SCOPES = ("department", "building", "multiple_buildings")


def _truncate(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text[:limit] if text else None


async def _describe_new_images(
    session: AsyncSession, ticket: Ticket
) -> None:
    """Описывает новые изображения vision-моделью перед анализом."""

    rows = (
        await session.scalars(
            select(TicketAttachment).where(
                TicketAttachment.ticket_id == ticket.id,
                TicketAttachment.kind == "image",
                TicketAttachment.description.is_(None),
                TicketAttachment.data.is_not(None),
            )
        )
    ).all()

    changed = False
    for row in rows:
        description = await describe_attachment(
            row.data or b"", row.mime_type
        )
        if description:
            row.description = description
            changed = True

    if changed:
        await session.commit()


async def build_analysis_request(
    session: AsyncSession,
    ticket: Ticket,
    extra_text: str | None = None,
) -> AnalysisRequest:
    """Собирает входной контракт из сообщений, звонков и вложений."""

    messages: list[AIMessage] = []

    rows = (
        await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == ticket.chat_session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        )
    ).all()

    for row in rows:
        if not row.content.strip():
            continue
        role = "client" if row.role == "user" else "bot"
        messages.append(AIMessage(role=role, text=row.content))

    if not messages and ticket.raw_text.strip():
        messages.append(AIMessage(role="client", text=ticket.raw_text))

    calls = (
        await session.scalars(
            select(Call)
            .where(
                Call.ticket_id == ticket.id,
                Call.transcript_text.is_not(None),
            )
            .order_by(Call.id)
        )
    ).all()

    for call in calls:
        transcript = (call.transcript_text or "").strip()
        if transcript:
            messages.append(
                AIMessage(
                    role="client",
                    text=f"Расшифровка телефонного звонка: {transcript}",
                )
            )

    if extra_text and extra_text.strip():
        messages.append(AIMessage(role="client", text=extra_text.strip()))

    if not messages:
        messages.append(AIMessage(role="client", text=ticket.raw_text))

    attachments = (
        await session.scalars(
            select(TicketAttachment)
            .options(defer(TicketAttachment.data))
            .where(TicketAttachment.ticket_id == ticket.id)
            .order_by(TicketAttachment.id)
        )
    ).all()

    ai_attachments = [
        AIAttachment(
            attachment_id=str(attachment.id),
            type=attachment.kind,  # type: ignore[arg-type]
            storage_path=f"db://attachments/{attachment.id}",
            mime_type=attachment.mime_type,
            description=attachment.description,
        )
        for attachment in attachments
        if attachment.kind in ("image", "audio", "document")
    ]

    source = "phone" if ticket.channel == "voice" else "chat"

    return AnalysisRequest(
        ticket_id=str(ticket.id),
        source=source,  # type: ignore[arg-type]
        messages=messages,
        taxonomy_version=TAXONOMY_VERSION,
        taxonomy=get_taxonomy(),
        attachments=ai_attachments,
        operator_overrides=OperatorOverrides(),
    )


def render_summary(result: TicketAIResult) -> str:
    """Человекочитаемая сводка для диспетчера и инженера."""

    lines: list[str] = []

    category = category_name(result.classification.category_code)
    subcategory = subcategory_by_code(
        result.classification.category_code,
        result.classification.subcategory_code,
    )
    if subcategory:
        lines.append(f"Категория: {category} / {subcategory.name}")
    else:
        lines.append(f"Категория: {category}")

    if result.issue.description:
        lines.append(result.issue.description)

    if result.issue.symptoms:
        names = [SYMPTOMS.get(code, code) for code in result.issue.symptoms]
        lines.append("Симптомы: " + ", ".join(names))

    if result.issue.attempted_actions:
        names = [
            ATTEMPTED_ACTIONS.get(code, code)
            for code in result.issue.attempted_actions
        ]
        lines.append("Уже выполнено: " + ", ".join(names))

    if result.issue.impact.scope != "unknown":
        scope = _IMPACT_LABELS.get(
            result.issue.impact.scope, result.issue.impact.scope
        )
        lines.append(f"Масштаб: {scope}")

    if result.intake.missing_fields:
        labels = [
            FIELD_LABELS.get(field, field)
            for field in result.intake.missing_fields
        ]
        lines.append("Не хватает данных: " + ", ".join(labels))

    if result.intake.questions_to_client:
        questions = "; ".join(
            question.question
            for question in result.intake.questions_to_client
        )
        lines.append(f"Уточнить: {questions}")

    lines.append(f"Уверенность ИИ: {result.confidence.overall:.0%}")
    return "\n".join(lines)


async def latest_analysis(
    session: AsyncSession, ticket: Ticket
) -> TicketAnalysis | None:
    return await session.scalar(
        select(TicketAnalysis)
        .where(TicketAnalysis.chat_session_id == ticket.chat_session_id)
        .order_by(TicketAnalysis.version.desc())
        .limit(1)
    )


def analysis_result(analysis: TicketAnalysis | None) -> TicketAIResult | None:
    if analysis is None or not isinstance(analysis.result, dict):
        return None
    try:
        return TicketAIResult.model_validate(analysis.result)
    except ValidationError:
        return None


async def _apply_classification(
    session: AsyncSession, ticket: Ticket, result: TicketAIResult
) -> None:
    classification = result.classification

    category = await session.scalar(
        select(Category).where(Category.code == classification.category_code)
    )
    ticket.category_id = category.id if category else None
    ticket.subcategory_id = None

    subcategory_code = classification.subcategory_code
    if (
        category is not None
        and subcategory_code
        and subcategory_code != "none"
    ):
        subcategory = await session.scalar(
            select(Subcategory).where(
                Subcategory.category_id == category.id,
                Subcategory.code == subcategory_code,
            )
        )
        ticket.subcategory_id = subcategory.id if subcategory else None


def _apply_result(ticket: Ticket, result: TicketAIResult) -> None:
    extracted = result.extracted_fields

    ticket.priority = (
        result.priority.suggested
        if result.priority.suggested in TICKET_PRIORITIES
        else None
    )
    ticket.symptoms = list(result.issue.symptoms)
    ticket.attempted_actions = list(result.issue.attempted_actions)
    ticket.missing_fields = list(result.intake.missing_fields)

    ticket.device = _truncate(extracted.device or extracted.object, 100)
    ticket.building = _truncate(extracted.location.building, 100)
    ticket.floor = _truncate(extracted.location.floor, 30)
    ticket.room = _truncate(extracted.location.room, 50)
    ticket.host = _truncate(extracted.hostname, 255)

    ticket.is_mass_incident = (
        result.issue.impact.scope in _MASS_SCOPES
    )
    ticket.needs_human_review = result.needs_human_review

    if ticket.status == "draft":
        ticket.status = "new"


async def analyze_ticket(
    session: AsyncSession,
    ticket: Ticket,
    *,
    force: bool = False,
    call_id: int | None = None,
    extra_text: str | None = None,
) -> TicketAIResult:
    """Запускает ИИ, сохраняет результат и обновляет заявку."""

    if not force:
        cached = analysis_result(await latest_analysis(session, ticket))
        if cached is not None:
            return cached

    await _describe_new_images(session, ticket)
    request = await build_analysis_request(session, ticket, extra_text)
    analyzer = get_analyzer()
    result = await analyzer.analyze(request)

    await _apply_classification(session, ticket, result)
    _apply_result(ticket, result)

    max_version = await session.scalar(
        select(TicketAnalysis.version)
        .where(TicketAnalysis.chat_session_id == ticket.chat_session_id)
        .order_by(TicketAnalysis.version.desc())
        .limit(1)
    )

    session.add(
        TicketAnalysis(
            chat_session_id=ticket.chat_session_id,
            ticket_id=ticket.id,
            version=(max_version or 0) + 1,
            model_name=analyzer.last_model or analyzer.last_provider,
            result=result.model_dump(mode="json"),
            confidence=result.confidence.overall,
        )
    )

    await session.commit()
    await session.refresh(ticket)
    return result


async def analyze_free_text(text: str, source: str = "chat") -> TicketAIResult:
    """Анализ текста без сохранения заявки (демо и тесты)."""

    request = AnalysisRequest(
        ticket_id="preview",
        source=source,  # type: ignore[arg-type]
        messages=[AIMessage(role="client", text=text)],
        taxonomy_version=TAXONOMY_VERSION,
        taxonomy=get_taxonomy(),
    )
    return await get_analyzer().analyze(request)
