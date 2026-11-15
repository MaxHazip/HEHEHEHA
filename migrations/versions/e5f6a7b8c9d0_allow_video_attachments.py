"""allow video attachments

Revision ID: e5f6a7b8c9d0
Revises: d1f2a3b4c5d6
Create Date: 2026-11-16
"""

from typing import Sequence, Union

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("ticket_attachments") as batch_op:
        batch_op.drop_constraint(
            "ck_ticket_attachments_kind", type_="check"
        )
        batch_op.create_check_constraint(
            "ck_ticket_attachments_kind",
            "kind IN ('image', 'audio', 'video', 'document')",
        )


def downgrade() -> None:
    with op.batch_alter_table("ticket_attachments") as batch_op:
        batch_op.drop_constraint(
            "ck_ticket_attachments_kind", type_="check"
        )
        batch_op.create_check_constraint(
            "ck_ticket_attachments_kind",
            "kind IN ('image', 'audio', 'document')",
        )
