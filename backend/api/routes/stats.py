"""Статистика для дашбордов диспетчера и руководителя."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_session
from backend.models import (
    Call,
    Category,
    Engineer,
    KnowledgeArticle,
    Ticket,
    TicketAnalysis,
)
from backend.schemas.stats_schemas import (
    CallsStats,
    CountItem,
    EngineersStats,
    HourlyItem,
    StatsResponse,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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

    closed_statuses = ("resolved", "closed")
    new_tickets = status_counts.get("new", 0) + status_counts.get("draft", 0)
    in_progress_tickets = status_counts.get("in_progress", 0)
    closed_tickets = status_counts.get("closed", 0) + status_counts.get(
        "resolved", 0
    )

    high_priority_tickets = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.priority.in_(("high", "critical")),
                Ticket.status.not_in(closed_statuses),
            )
        )
        or 0
    )

    unassigned_tickets = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.engineer_id.is_(None),
                Ticket.status.not_in(closed_statuses),
            )
        )
        or 0
    )

    sla_risks = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.status.not_in(closed_statuses),
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

    engineers_total = int(
        await session.scalar(select(func.count(Engineer.id))) or 0
    )
    engineers_available = int(
        await session.scalar(
            select(func.count(Engineer.id)).where(Engineer.available.is_(True))
        )
        or 0
    )
    engineers_load = int(
        await session.scalar(select(func.coalesce(func.sum(Engineer.load), 0)))
        or 0
    )

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
        hourly.append(
            HourlyItem(time=label, tickets=buckets.get(label, 0))
        )

    completion_rate = (
        round(closed_tickets / total_tickets * 100, 1)
        if total_tickets
        else 0.0
    )

    return StatsResponse(
        total_tickets=total_tickets,
        new_tickets=new_tickets,
        in_progress_tickets=in_progress_tickets,
        closed_tickets=closed_tickets,
        high_priority_tickets=high_priority_tickets,
        unassigned_tickets=unassigned_tickets,
        sla_risks=sla_risks,
        completion_rate=completion_rate,
        avg_ai_confidence=round(float(avg_confidence or 0) * 100, 1),
        manual_edits=manual_edits,
        by_status=[
            CountItem(name=status, count=count)
            for status, count in sorted(status_counts.items())
        ],
        by_priority=[
            CountItem(name=priority, count=count)
            for priority, count in priority_counts.items()
        ],
        by_category=[
            CountItem(name=str(name), count=int(count))
            for name, count in category_rows
        ],
        hourly=hourly,
        engineers=EngineersStats(
            total=engineers_total,
            available=engineers_available,
            load=engineers_load,
        ),
        calls=CallsStats(
            total=calls_total,
            today=calls_today,
            with_recording=calls_with_recording,
        ),
        knowledge_articles=knowledge_articles,
        generated_at=now,
    )
