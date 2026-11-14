"""Store dispatcher edits separately from the AI analysis history."""

import sqlalchemy as sa
from alembic import op

revision = "b73bd8b594a3"
down_revision = "af9ae7627311"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("reviewed_description", sa.Text()))


def downgrade() -> None:
    op.drop_column("tickets", "reviewed_description")
