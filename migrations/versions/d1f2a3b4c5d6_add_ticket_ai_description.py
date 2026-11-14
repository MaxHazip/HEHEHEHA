"""add ticket ai_description

Revision ID: d1f2a3b4c5d6
Revises: c6b3447844da
Create Date: 2026-11-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "c6b3447844da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("ai_description", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tickets", "ai_description")
