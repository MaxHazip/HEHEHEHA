"""Профиль инженера: компетенции и текущая нагрузка."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base
from backend.models._types import big_int, text_array

if TYPE_CHECKING:
    from backend.models.ticket import Ticket
    from backend.models.user import User


class Engineer(Base):
    __tablename__ = "engineers"

    __table_args__ = (
        CheckConstraint(
            "load >= 0",
            name="ck_engineers_load_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(big_int(), primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        big_int(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    competencies: Mapped[list[str]] = mapped_column(
        text_array(),
        nullable=False,
        default=list,
    )

    load: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="engineer",
    )

    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="engineer",
        foreign_keys="Ticket.engineer_id",
    )

    recommended_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="recommended_engineer",
        foreign_keys="Ticket.recommended_engineer_id",
    )
