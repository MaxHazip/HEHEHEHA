
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.ticket import Ticket
    from backend.models.knowledge_article_models import KnowledgeArticle


class TicketKBArticle(Base):
    __tablename__ = "ticket_kb_articles"

    __table_args__ = (
        CheckConstraint(
            "relevance_score >= 0 AND relevance_score <= 1",
            name="ck_ticket_kb_articles_relevance_score",
        ),
    )

    ticket_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    )

    article_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_articles.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    relevance_score: Mapped[float | None] = mapped_column(
        Float(precision=53),
        nullable=True,
    )

    ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        back_populates="kb_recommendations",
    )

    article: Mapped["KnowledgeArticle"] = relationship(
        "KnowledgeArticle",
        back_populates="ticket_recommendations",
    )
