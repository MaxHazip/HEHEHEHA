"""Engineer and article recommendations and a deadline-based SLA estimate."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Engineer, KnowledgeArticle, Ticket, TicketKBArticle, User

SLA_HOURS = {"critical": 2, "high": 8, "medium": 24, "low": 72}
DONE = {"resolved", "closed"}
ARTICLES = (
    ("network", "Нет подключения к сети", "Уточните масштаб сбоя. Проверьте соединение, параметры IP и доступность шлюза."),
    ("hardware", "Диагностика оборудования", "Уточните модель устройства. Проверьте питание, подключение и индикаторы."),
    ("software", "Ошибка приложения", "Зафиксируйте текст ошибки, версию приложения и шаги для воспроизведения."),
    ("access", "Проблемы со входом", "Уточните сервис и текст ошибки. Проверьте статус учётной записи."),
)


async def seed_articles(session: AsyncSession) -> None:
    existing = set(await session.scalars(select(KnowledgeArticle.code)))
    for code, title, body in ARTICLES:
        if code not in existing:
            session.add(KnowledgeArticle(code=code, title=title, body=body, keywords=[code]))
    await session.commit()


async def recommend(session: AsyncSession, ticket: Ticket, category: str, subcategory: str) -> None:
    tags = {category, subcategory} - {"none", "", None}
    load = (
        select(func.count(Ticket.id))
        .where(Ticket.engineer_id == Engineer.id, Ticket.status.not_in(DONE))
        .correlate(Engineer)
        .scalar_subquery()
    )
    engineers = (await session.execute(
        select(Engineer, load).join(User, Engineer.user_id == User.id)
        .where(Engineer.available.is_(True), User.is_active.is_(True), User.role == "engineer")
    )).all()
    candidates = [row for row in engineers if tags.intersection(row[0].competencies)]
    best = min(candidates, key=lambda row: (-len(tags.intersection(row[0].competencies)), row[1], row[0].id), default=None)
    ticket.recommended_engineer_id = best[0].id if best else None

    await session.execute(delete(TicketKBArticle).where(TicketKBArticle.ticket_id == ticket.id))
    for article in await session.scalars(select(KnowledgeArticle)):
        matches = tags.intersection(article.keywords)
        if matches:
            session.add(TicketKBArticle(
                ticket_id=ticket.id, article_id=article.id, relevance_score=len(matches) / len(tags),
            ))


def sla(ticket: Ticket) -> tuple[datetime, str]:
    created = ticket.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    duration = timedelta(hours=SLA_HOURS[ticket.priority or "medium"])
    deadline = created + duration
    if ticket.status in DONE:
        return deadline, "complete"
    remaining = deadline - datetime.now(timezone.utc)
    if remaining <= timedelta():
        return deadline, "overdue"
    if remaining <= duration / 4:
        return deadline, "at_risk"
    return deadline, "on_track"
