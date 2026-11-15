"""Автоназначение инженера по категории заявки."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Category, Engineer, Ticket

logger = logging.getLogger(__name__)

CLOSED_STATUSES = ("resolved", "closed")


async def assign_engineer_for_ticket(
    session: AsyncSession,
    ticket: Ticket,
    *,
    force: bool = False,
    commit: bool = False,
) -> Engineer | None:
    """Назначает инженера с нужной компетенцией и минимальной загрузкой."""

    if ticket.category_id is None:
        return None

    if ticket.engineer_id is not None and not force:
        return await session.get(Engineer, ticket.engineer_id)

    category = await session.get(Category, ticket.category_id)
    if category is None:
        return None

    engineers = (await session.scalars(select(Engineer))).all()
    if not engineers:
        return None

    open_rows = (
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
        for engineer_id, count in open_rows
        if engineer_id is not None
    }

    candidates = [
        engineer
        for engineer in engineers
        if engineer.available
        and category.code in (engineer.competencies or [])
    ]
    if not candidates:
        # Фолбэк: если под категорию нет компетенции — наименее загруженный.
        candidates = [
            engineer for engineer in engineers if engineer.available
        ]
    if not candidates:
        return None

    chosen = min(
        candidates,
        key=lambda engineer: (
            open_by_engineer.get(engineer.id, 0),
            engineer.load or 0,
            engineer.id,
        ),
    )

    ticket.engineer_id = chosen.id
    await session.flush()

    open_count = int(
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.engineer_id == chosen.id,
                Ticket.status.not_in(CLOSED_STATUSES),
            )
        )
        or 0
    )
    chosen.load = open_count

    if commit:
        await session.commit()
        await session.refresh(chosen)

    logger.info(
        "Заявка %s назначена инженеру %s (%s)",
        ticket.id,
        chosen.id,
        category.code,
    )
    return chosen
