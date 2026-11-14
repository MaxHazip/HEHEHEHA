
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base

if TYPE_CHECKING:
    from backend.models.categories_models import Category
    from backend.models.ticket import Ticket


class Subcategory(Base):
    __tablename__ = "subcategories"

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "code",
            name="uq_subcategories_category_code",
        ),
        CheckConstraint(
            "length(btrim(code)) > 0",
            name="ck_subcategories_code_not_blank",
        ),
        CheckConstraint(
            "length(btrim(name)) > 0",
            name="ck_subcategories_name_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="subcategories",
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="subcategory",
    )
