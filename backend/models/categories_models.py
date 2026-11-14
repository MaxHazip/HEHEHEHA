
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.subcategories_models import Subcategory
    from backend.models.ticket import Ticket


class Category(Base):
    __tablename__ = "categories"

    __table_args__ = (
        CheckConstraint(
            "length(btrim(code)) > 0",
            name="ck_categories_code_not_blank",
        ),
        CheckConstraint(
            "length(btrim(name)) > 0",
            name="ck_categories_name_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    subcategories: Mapped[list["Subcategory"]] = relationship(
        "Subcategory",
        back_populates="category",
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="category",
    )
