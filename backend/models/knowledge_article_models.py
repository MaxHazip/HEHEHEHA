
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.ticket_kb_article_models import TicketKBArticle


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    __table_args__ = (
        CheckConstraint(
            "length(btrim(code)) > 0",
            name="ck_knowledge_articles_code_not_blank",
        ),
        CheckConstraint(
            "length(btrim(title)) > 0",
            name="ck_knowledge_articles_title_not_blank",
        ),
        CheckConstraint(
            "length(btrim(body)) > 0",
            name="ck_knowledge_articles_body_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("'{}'::text[]"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    ticket_recommendations: Mapped[list["TicketKBArticle"]] = relationship(
        "TicketKBArticle",
        back_populates="article",
    )
