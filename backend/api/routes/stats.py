"""Статистика для дашбордов диспетчера и руководителя."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_session
from backend.models import (
    Call,
    Category,
    Engineer,
    KnowledgeArticle,
    Subcategory,
    Ticket,
    TicketAnalysis,
    TicketAttachment,
    User,
)
from backend.schemas.stats_schemas import (
    AttachmentsStats,
    CallsStats,
    CountItem,
    DailyItem,
    EngineerLoadItem,
    EngineersStats,
    HourlyItem,
    StatsResponse,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CLOSED_STATUSES = ("resolved", "closed")


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _count_items(rows) -> list[CountItem]:
    return [
        CountItem(name=str(name), count=int(count))
        for name, count in rows
    ]


@router.get("", response_model=StatsResponse, summary="Статистика системы")
async def read_stats(session: SessionDep) -> StatsResponse:
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)

    total_tickets = int(
        await session.scalar(select(func.count(Ticket.id))) or 0
    )

    status_rows = (
        await session.execute(
            select(Ticket.status, func.count(Ticket.id)).group_by(
                Ticket.status
            )
        )
    ).all()
    status_counts = {
        str(status): int(count) for status, count in status_rows
    }

    priority_rows = (
        await session.execute(
            select(Ticket.priority, func.count(Ticket.id)).group_by(
                Ticket.priority
            )
        )
    ).all()
    priority_counts: dict[str, int] = {}
    for priority, count in priority_rows:
        priority_counts[str(priority or "none")] = int(count)

    category_rows = (
        await session.execute(
            select(Category.name, func.count(Ticket.id))
            .join(Ticket, Ticket.category_id == Category.id)
            .group_by(Category.name)
            .order_by(func.count(Ticket.id).desc())
        )
    ).all()

    subcategory_rows = (
        await session.execute(
            select(Subcategory.name, func.count(Ticket.id))
            .join(Ticket, Ticket.subcategory_id == Subcategory.id)
            .group_by(Subcategory.name)
            .order_by(func.count(Ticket.id).desc())
            .limit(12)
        )
    ).all()

    channel_rows = (
        await session.execute(
            select(Ticket.channel, func.count(Ticket.id)).group_by(
                Ticket.channel
            )
        )
    ).all()

    draft_tickets = status_counts.get("draft", 0)
    resolved_tickets = status_counts.get("resolved", 0)
    new_tickets = status_counts.get("new", 0)
    in_progress_tickets = status_counts.get("in_progress", 0)
    closed_tickets = status_counts.get("closed", 0) + resolved_tickets

    high_priority_tickets = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.priority.in_(("high", "critical")),
                Ticket.status.not_in(CLOSED_STATUSES),
            )
        )
        or 0
    )

    unassigned_tickets = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.engineer_id.is_(None),
                Ticket.status.not_in(CLOSED_STATUSES),
            )
        )
        or 0
    )

    ai_review_tickets = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.needs_human_review.is_(True),
                Ticket.status.not_in(CLOSED_STATUSES),
            )
        )
        or 0
    )

    mass_incident_tickets = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.is_mass_incident.is_(True)
            )
        )
        or 0
    )

    sla_risks = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.status.not_in(CLOSED_STATUSES),
                Ticket.created_at < day_ago,
            )
        )
        or 0
    )

    avg_confidence = await session.scalar(
        select(func.avg(TicketAnalysis.confidence)).where(
            TicketAnalysis.model_name != "rule-based"
        )
    )
    manual_edits = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.ai_description.is_not(None)
            )
        )
        or 0
    )

    engineer_rows = (
        await session.execute(
            select(Engineer, User)
            .join(User, Engineer.user_id == User.id)
            .order_by(User.name)
        )
    ).all()

    open_by_engineer_rows = (
        await session.execute(
            select(Ticket.engineer_id, func.count(Ticket.id))
            .where(
                Ticket.engineer_id.is_not(None),
                Ticket.status.not_in(CLOSED_STATUSES),
            )
            .group_by(Ticket.engineer_id)
        )
    ).all()
    open_by_engineer = {
        int(engineer_id): int(count)
        for engineer_id, count in open_by_engineer_rows
        if engineer_id is not None
    }

    engineers_detail = [
        EngineerLoadItem(
            id=engineer.id,
            name=user.name,
            competencies=list(engineer.competencies or []),
            load=open_by_engineer.get(engineer.id, 0),
            available=engineer.available,
            open_tickets=open_by_engineer.get(engineer.id, 0),
        )
        for engineer, user in engineer_rows
    ]

    engineers_total = len(engineers_detail)
    engineers_available = sum(
        1 for item in engineers_detail if item.available
    )
    engineers_load = sum(item.open_tickets for item in engineers_detail)

    calls_total = int(
        await session.scalar(select(func.count(Call.id))) or 0
    )
    calls_today = int(
        await session.scalar(
            select(func.count(Call.id)).where(Call.created_at >= day_ago)
        )
        or 0
    )
    calls_with_recording = int(
        await session.scalar(
            select(func.count(Call.id)).where(
                Call.recording_size.is_not(None)
            )
        )
        or 0
    )
    calls_with_transcript = int(
        await session.scalar(
            select(func.count(Call.id)).where(
                Call.transcript_text.is_not(None)
            )
        )
        or 0
    )

    attachment_rows = (
        await session.execute(
            select(TicketAttachment.kind, func.count(TicketAttachment.id))
            .group_by(TicketAttachment.kind)
        )
    ).all()
    attachment_counts = {
        str(kind): int(count) for kind, count in attachment_rows
    }
    attachments = AttachmentsStats(
        total=sum(attachment_counts.values()),
        images=attachment_counts.get("image", 0),
        audio=attachment_counts.get("audio", 0),
        video=attachment_counts.get("video", 0),
        documents=attachment_counts.get("document", 0),
    )

    knowledge_articles = int(
        await session.scalar(select(func.count(KnowledgeArticle.id))) or 0
    )

    # Почасовая нагрузка за последние 24 часа.
    created_rows = (
        await session.scalars(
            select(Ticket.created_at).where(Ticket.created_at >= day_ago)
        )
    ).all()
    buckets: dict[str, int] = {}
    for created_at in created_rows:
        if created_at is None:
            continue
        key = _as_aware(created_at).strftime("%H:00")
        buckets[key] = buckets.get(key, 0) + 1

    hour_start = now.replace(minute=0, second=0, microsecond=0)
    hourly: list[HourlyItem] = []
    for offset in range(23, -1, -1):
        moment = hour_start - timedelta(hours=offset)
        label = moment.strftime("%H:00")
        hourly.append(HourlyItem(time=label, tickets=buckets.get(label, 0)))

    # Дневная динамика за 14 дней.
    start_date = (now - timedelta(days=13)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    daily_rows = (
        await session.execute(
            select(
                Ticket.created_at,
                Ticket.updated_at,
                Ticket.status,
            ).where(
                or_(
                    Ticket.created_at >= start_date,
                    Ticket.updated_at >= start_date,
                )
            )
        )
    ).all()
    daily_buckets: dict[str, dict[str, int]] = {}
    for created_at, updated_at, status in daily_rows:
        if created_at is not None:
            created_dt = _as_aware(created_at)
            if created_dt >= start_date:
                key = created_dt.strftime("%d.%m")
                daily_buckets.setdefault(key, {"created": 0, "closed": 0})[
                    "created"
                ] += 1
        if status in CLOSED_STATUSES and updated_at is not None:
            updated_dt = _as_aware(updated_at)
            if updated_dt >= start_date:
                key = updated_dt.strftime("%d.%m")
                daily_buckets.setdefault(key, {"created": 0, "closed": 0})[
                    "closed"
                ] += 1

    daily: list[DailyItem] = []
    for offset in range(0, 14):
        moment = start_date + timedelta(days=offset)
        key = moment.strftime("%d.%m")
        bucket = daily_buckets.get(key, {"created": 0, "closed": 0})
        daily.append(
            DailyItem(
                date=key,
                created=bucket["created"],
                closed=bucket["closed"],
            )
        )

    resolution_rows = (
        await session.execute(
            select(Ticket.created_at, Ticket.updated_at).where(
                Ticket.status.in_(CLOSED_STATUSES)
            )
        )
    ).all()
    durations = []
    for created_at, updated_at in resolution_rows:
        if created_at is None or updated_at is None:
            continue
        delta = (
            _as_aware(updated_at) - _as_aware(created_at)
        ).total_seconds() / 3600
        if delta >= 0:
            durations.append(delta)
    avg_resolution_hours = (
        round(sum(durations) / len(durations), 1) if durations else 0.0
    )

    completion_rate = (
        round(closed_tickets / total_tickets * 100, 1)
        if total_tickets
        else 0.0
    )

    return StatsResponse(
        total_tickets=total_tickets,
        new_tickets=new_tickets,
        draft_tickets=draft_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        closed_tickets=closed_tickets,
        high_priority_tickets=high_priority_tickets,
        unassigned_tickets=unassigned_tickets,
        ai_review_tickets=ai_review_tickets,
        mass_incident_tickets=mass_incident_tickets,
        sla_risks=sla_risks,
        completion_rate=completion_rate,
        avg_ai_confidence=round(float(avg_confidence or 0) * 100, 1),
        avg_resolution_hours=avg_resolution_hours,
        manual_edits=manual_edits,
        by_status=_count_items(
            sorted(status_counts.items())
        ),
        by_priority=_count_items(priority_counts.items()),
        by_category=_count_items(category_rows),
        by_subcategory=_count_items(subcategory_rows),
        by_channel=_count_items(channel_rows),
        hourly=hourly,
        daily=daily,
        engineers=EngineersStats(
            total=engineers_total,
            available=engineers_available,
            load=engineers_load,
        ),
        engineers_detail=engineers_detail,
        calls=CallsStats(
            total=calls_total,
            today=calls_today,
            with_recording=calls_with_recording,
            with_transcript=calls_with_transcript,
        ),
        attachments=attachments,
        knowledge_articles=knowledge_articles,
        generated_at=now,
    )
