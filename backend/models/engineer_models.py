
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.user_models import User
    from backend.models.ticket import Ticket


class Engineer(Base):
    __tablename__ = "engineers"

    __table_args__ = (
        CheckConstraint(
            "load >= 0",
            name="ck_engineers_load_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    competencies: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("'{}'::text[]"),
    )

    load: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
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
