"""Связка backend-моделей и ИИ-модуля."""

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
from backend.core.settings import settings
from backend.models import (
    AIAnalysisRecord,
    Call,
    Ticket,
    TicketAttachment,
    TicketMessage,
)

logger = logging.getLogger(__name__)

GENERIC_TITLES = {
    "Новое обращение",
    "Обращение",
    "Звонок",
    "Обращение по телефону",
}

_IMPACT_LABELS = {
    "single_device": "одно устройство",
    "single_user": "один пользователь",
    "department": "отдел",
    "building": "здание",
    "multiple_buildings": "несколько зданий",
    "unknown": "неизвестно",
}


async def _describe_new_images(
    session: AsyncSession, ticket: Ticket
) -> None:
    """Описывает новые скриншоты vision-моделью перед анализом.

    Работает только при настроенном Google-ключе: без него описание
    не выдумывается, а анализ идёт по тексту.
    """

    if not settings.google_api_key:
        return

    rows = (
        await session.scalars(
            select(TicketAttachment).where(
                TicketAttachment.ticket_id == ticket.id,
                TicketAttachment.kind == "image",
                TicketAttachment.description.is_(None),
            )
        )
    ).all()

    changed = False
    for row in rows:
        description = await describe_attachment(row.data, row.mime_type)
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
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.id)
        )
    ).all()

    for row in rows:
        if not row.text.strip():
            continue
        role = row.role if row.role in ("client", "bot", "dispatcher") else "dispatcher"
        messages.append(AIMessage(role=role, text=row.text))

    if not messages and ticket.description.strip():
        messages.append(AIMessage(role="client", text=ticket.description))

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
        messages.append(AIMessage(role="client", text=ticket.title))

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

    source = ticket.source if ticket.source in ("chat", "web", "phone") else "chat"

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


def build_title(result: TicketAIResult) -> str:
    category = category_name(result.classification.category_code)
    subcategory = subcategory_by_code(
        result.classification.category_code,
        result.classification.subcategory_code,
    )
    room = result.extracted_fields.location.room

    title = category
    if subcategory:
        title = f"{category}: {subcategory.name}"
    if room:
        title = f"{title} — каб. {room}"
    return title[:120]


async def analyze_ticket(
    session: AsyncSession,
    ticket: Ticket,
    *,
    force: bool = False,
    call_id: int | None = None,
    extra_text: str | None = None,
) -> TicketAIResult:
    """Запускает ИИ, сохраняет результат и обновляет заявку."""

    if ticket.ai_analysis and not force:
        try:
            return TicketAIResult.model_validate(ticket.ai_analysis)
        except ValidationError:
            logger.warning(
                "Сохранённый анализ заявки %s не прошёл валидацию, пересчитываем.",
                ticket.id,
            )

    await _describe_new_images(session, ticket)
    request = await build_analysis_request(session, ticket, extra_text)
    analyzer = get_analyzer()
    result = await analyzer.analyze(request)

    ticket.ai_analysis = result.model_dump(mode="json")
    ticket.category_code = result.classification.category_code
    ticket.subcategory_code = result.classification.subcategory_code
    ticket.priority = result.priority.suggested
    ticket.needs_human_review = result.needs_human_review
    ticket.ai_confidence = result.confidence.overall
    ticket.ai_description = render_summary(result)
    ticket.ai_solution = (
        "\n".join(result.decision_notes) if result.decision_notes else None
    )

    if not ticket.title.strip() or ticket.title in GENERIC_TITLES:
        ticket.title = build_title(result)

    session.add(
        AIAnalysisRecord(
            ticket_id=ticket.id,
            call_id=call_id,
            schema_version=result.schema_version,
            provider=analyzer.last_provider,
            model=analyzer.last_model,
            result=result.model_dump(mode="json"),
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
