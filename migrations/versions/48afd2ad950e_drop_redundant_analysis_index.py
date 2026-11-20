"""Drop the index covered by the unique session/version constraint."""

from alembic import op

revision = "48afd2ad950e"
down_revision = "c6b3447844da"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "ix_ticket_analyses_chat_session_id",
        table_name="ticket_analyses",
        if_exists=True,
    )


def downgrade() -> None:
    op.create_index(
        "ix_ticket_analyses_chat_session_id",
        "ticket_analyses",
        ["chat_session_id"],
    )
