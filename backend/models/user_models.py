
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.engineer_models import Engineer
    from backend.models.chat_session import ChatSession
    from backend.models.ticket import Ticket


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('requester', 'dispatcher', 'engineer')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "length(btrim(name)) > 0",
            name="ck_users_name_not_blank",
        )
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    engineer: Mapped["Engineer | None"] = relationship(
        "Engineer",
        back_populates="user",
        uselist=False,
    )

    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="creator",
        foreign_keys="Ticket.created_by",
    )

    confirmed_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="confirmer",
        foreign_keys="Ticket.confirmed_by",
    )
