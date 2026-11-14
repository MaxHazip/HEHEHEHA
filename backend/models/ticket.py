from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base  

if TYPE_CHECKING:
    from backend.models.categories_models import Category
    from backend.models.chat_session import ChatSession
    from backend.models.engineer_models import Engineer
    from backend.models.subcategories_models import Subcategory
    from backend.models.user_models import User
    from backend.models.ticket_analysis import TicketAnalysis
    from backend.models.ticket_event import TicketEvent
    from backend.models.ticket_kb_article_models import TicketKBArticle
    from backend.models.ticket_attachment import TicketAttachment


class TicketStatuses(str, enum.Enum):
    DRAFT = "draft"
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriorities(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketChannels(str, enum.Enum):
    CHAT = "chat"
    VOICE = "voice"
    IMAGE = "image"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,                   
    )

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    channel: Mapped[TicketChannels] = mapped_column(
        Enum(
            TicketChannels,
            name="ticket_channel_enum",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    status: Mapped[TicketStatuses] = mapped_column(
        Enum(
            TicketStatuses,
            name="ticket_status_enum",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=TicketStatuses.DRAFT,
        server_default=TicketStatuses.DRAFT.value,
        index=True,                   
    )

    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),  
        nullable=True,
    )
    subcategory_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("subcategories.id", ondelete="RESTRICT"),  
        nullable=True,
    )

    priority: Mapped[TicketPriorities | None] = mapped_column(
        Enum(
            TicketPriorities,
            name="ticket_priority_enum",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )

    device: Mapped[str | None] = mapped_column(String(100), nullable=True)
    building: Mapped[str | None] = mapped_column(String(100), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(30), nullable=True)
    room: Mapped[str | None] = mapped_column(String(50), nullable=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)

    symptoms: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False,
        server_default=text("'{}'::text[]"),
    )
    attempted_actions: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False,
        server_default=text("'{}'::text[]"),
    )
    missing_fields: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False,
        server_default=text("'{}'::text[]"),
    )

    is_mass_incident: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    needs_human_review: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    recommended_engineer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("engineers.id", ondelete="SET NULL"),
        nullable=True,
    )
    engineer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("engineers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,              
    )
    confirmed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column( 
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    chat_session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="ticket",
    )
    creator: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], back_populates="tickets",
    )
    confirmer: Mapped["User | None"] = relationship(
        "User", foreign_keys=[confirmed_by], back_populates="confirmed_tickets",
    )
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="tickets",
    )
    subcategory: Mapped["Subcategory | None"] = relationship(
        "Subcategory", back_populates="tickets",
    )
    engineer: Mapped["Engineer | None"] = relationship(
        "Engineer", foreign_keys=[engineer_id], back_populates="assigned_tickets",
    )
    recommended_engineer: Mapped["Engineer | None"] = relationship(
        "Engineer",
        foreign_keys=[recommended_engineer_id],
        back_populates="recommended_tickets",
    )

    analyses: Mapped[list["TicketAnalysis"]] = relationship(
        "TicketAnalysis",
        back_populates="ticket",
    )

    events: Mapped[list["TicketEvent"]] = relationship(
        "TicketEvent",
        back_populates="ticket",
        order_by="TicketEvent.created_at",
    )

    kb_recommendations: Mapped[list["TicketKBArticle"]] = relationship(
        "TicketKBArticle",
        back_populates="ticket",
    )

    attachments: Mapped[list["TicketAttachment"]] = relationship(
        "TicketAttachment",
        back_populates="ticket",
    )