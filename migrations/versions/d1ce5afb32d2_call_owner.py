"""Record the authenticated user who started a browser call."""

import sqlalchemy as sa
from alembic import context, op

from migrations.versions.c6b3447844da_init import create_calls_table, create_transcript_table

revision = "d1ce5afb32d2"
down_revision = "b73bd8b594a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Some deployments applied the initial revision before telephony was added.
    if not context.is_offline_mode():
        inspector = sa.inspect(op.get_bind())
        if not inspector.has_table("calls"):
            create_calls_table()
        if not inspector.has_table("call_transcript_segments"):
            create_transcript_table()

    with op.batch_alter_table("calls") as batch:
        batch.add_column(sa.Column("created_by", sa.BigInteger().with_variant(sa.Integer(), "sqlite")))
        batch.create_foreign_key("fk_calls_created_by", "users", ["created_by"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("calls") as batch:
        batch.drop_constraint("fk_calls_created_by", type_="foreignkey")
        batch.drop_column("created_by")
