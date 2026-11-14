# from datetime import datetime
# from typing import TYPE_CHECKING

# from sqlalchemy import (
#     BigInteger,
#     Boolean,
#     CheckConstraint,
#     DateTime,
#     Index,
#     String,
#     func,
#     text,
# )
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from backend.core.database import Base

# if TYPE_CHECKING:
#     from backend.models.engineer_models import Engineer
#     from backend.models.chat_session import ChatSession
#     from backend.models.ticket import Ticket
#     from backend.models.ticket_event import TicketEvent


# class User(Base):
#     __tablename__ = "users"

#     __table_args__ = (
#         CheckConstraint(
#             "role IN ('requester', 'dispatcher', 'engineer')",
#             name="ck_users_role",
#         ),
#         CheckConstraint(
#             "length(btrim(name)) > 0",
#             name="ck_users_name_not_blank",
#         )
#     )

#     id: Mapped[int] = mapped_column(
#         BigInteger,
#         primary_key=True,
#         autoincrement=True,
#     )

#     name: Mapped[str] = mapped_column(
#         String(150),
#         nullable=False,
#     )

#     password_hash: Mapped[str] = mapped_column(
#         String(255),
#         nullable=False,
#     )

#     role: Mapped[str] = mapped_column(
#         String(20),
#         nullable=False,
#     )

#     is_active: Mapped[bool] = mapped_column(
#         Boolean,
#         nullable=False,
#         server_default=text("true"),
#     )

#     phone: Mapped[str] = mapped_column(
#         String(16),
#         nullable=False,
#         unique=True,
#     )

#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         nullable=False,
#         server_default=func.now(),
#     )

#     engineer: Mapped["Engineer | None"] = relationship(
#         "Engineer",
#         back_populates="user",
#         uselist=False,
#     )

#     chat_sessions: Mapped[list["ChatSession"]] = relationship(
#         "ChatSession",
#         back_populates="user",
#     )

#     tickets: Mapped[list["Ticket"]] = relationship(
#         "Ticket",
#         back_populates="creator",
#         foreign_keys="Ticket.created_by",
#     )

#     confirmed_tickets: Mapped[list["Ticket"]] = relationship(
#         "Ticket",
#         back_populates="confirmer",
#         foreign_keys="Ticket.confirmed_by",
#     )

#     ticket_events: Mapped[list["TicketEvent"]] = relationship(
#         "TicketEvent",
#         back_populates="actor",
#     )

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Пользователь системы: клиент, диспетчер, инженер или админ."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(
        String(32), unique=True, index=True, default=None
    )
    # client | dispatcher | engineer | admin
    role: Mapped[str] = mapped_column(String(20), default="client", index=True)
    specialty: Mapped[str | None] = mapped_column(String(120), default=None)
    password_hash: Mapped[str | None] = mapped_column(String(255), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
