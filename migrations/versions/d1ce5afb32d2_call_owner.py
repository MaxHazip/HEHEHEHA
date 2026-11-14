"""Record the authenticated user who started a browser call."""

import sqlalchemy as sa
from alembic import op

revision = "d1ce5afb32d2"
down_revision = "b73bd8b594a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("calls") as batch:
        batch.add_column(sa.Column("created_by", sa.BigInteger().with_variant(sa.Integer(), "sqlite")))
        batch.create_foreign_key("fk_calls_created_by", "users", ["created_by"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("calls") as batch:
        batch.drop_constraint("fk_calls_created_by", type_="foreignkey")
        batch.drop_column("created_by")
