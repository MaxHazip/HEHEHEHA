"""Switch accounts to phone numbers, preserving account IDs and references."""

import sqlalchemy as sa
from alembic import context, op

revision = "af9ae7627311"
down_revision = "48afd2ad950e"
branch_labels = None
depends_on = None

DEMO_PHONES = {
    "admin": "+79990000001",
    "dispatcher": "+79991234567",
    "network": "+73213211212",
    "hardware": "+79992345678",
    "software": "+79993456789",
    "requester": "+79994567890",
}


def _upgrade_legacy_postgresql() -> bool:
    """Handle the original PostgreSQL schema that already used phones."""
    if context.is_offline_mode() or op.get_context().dialect.name != "postgresql":
        return False
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"]: column for column in inspector.get_columns("users")}
    if "phone" not in columns or "email" in columns or "legacy_email" in columns:
        return False

    op.add_column("users", sa.Column("legacy_email", sa.String(255), nullable=True))
    op.alter_column(
        "users", "phone", existing_type=columns["phone"]["type"],
        type_=sa.String(32), nullable=False,
    )
    checks = {item["name"] for item in inspector.get_check_constraints("users")}
    if "ck_users_role" in checks:
        op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint(
        "ck_users_role", "users", "role IN ('requester', 'dispatcher', 'engineer', 'admin')",
    )
    if "ck_users_phone_not_blank" not in checks:
        op.create_check_constraint("ck_users_phone_not_blank", "users", "length(trim(phone)) > 0")

    unique = {
        item["name"] for item in inspector.get_unique_constraints("users")
        if item["column_names"] == ["phone"]
    }
    if "uq_users_phone" not in unique:
        if "users_phone_key" in unique:
            op.execute("ALTER TABLE users RENAME CONSTRAINT users_phone_key TO uq_users_phone")
        else:
            op.create_unique_constraint("uq_users_phone", "users", ["phone"])
    return True


def upgrade() -> None:
    if _upgrade_legacy_postgresql():
        return

    op.add_column("users", sa.Column("phone", sa.String(32), nullable=True))
    users = sa.table("users", sa.column("id", sa.BigInteger()), sa.column("email", sa.String(255)), sa.column("phone", sa.String(32)))
    for name, phone in DEMO_PHONES.items():
        op.execute(
            users.update().where(sa.func.lower(users.c.email) == f"{name}@dispatch.local")
            .values(phone=phone)
        )
    # Legacy accounts have no recoverable phone. Keep their references and
    # reserve an internal identifier until an operator sets a real number.
    op.execute(
        users.update().where(users.c.phone.is_(None))
        .values(phone=sa.literal("legacy:") + sa.cast(users.c.id, sa.String()))
    )
    op.drop_index("uq_users_email_lower", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("ck_users_role", type_="check")
        batch.create_check_constraint("ck_users_role", "role IN ('requester', 'dispatcher', 'engineer', 'admin')")
        batch.drop_constraint("ck_users_email_not_blank", type_="check")
        batch.alter_column("email", new_column_name="legacy_email", existing_type=sa.String(255), nullable=True)
        batch.alter_column("phone", existing_type=sa.String(32), nullable=False)
        batch.create_unique_constraint("uq_users_phone", ["phone"])
        batch.create_check_constraint("ck_users_phone_not_blank", "length(trim(phone)) > 0")


def downgrade() -> None:
    users = sa.table("users", sa.column("id", sa.BigInteger()), sa.column("legacy_email", sa.String(255)))
    op.execute(users.update().where(users.c.legacy_email.is_(None)).values(
        legacy_email=sa.literal("rollback-") + sa.cast(users.c.id, sa.String()) + "@dispatch.invalid"
    ))
    op.execute("UPDATE users SET role = 'dispatcher' WHERE role = 'admin'")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("ck_users_role", type_="check")
        batch.create_check_constraint("ck_users_role", "role IN ('requester', 'dispatcher', 'engineer')")
        batch.drop_constraint("uq_users_phone", type_="unique")
        batch.drop_constraint("ck_users_phone_not_blank", type_="check")
        batch.drop_column("phone")
        batch.alter_column("legacy_email", new_column_name="email", existing_type=sa.String(255), nullable=False)
        batch.create_check_constraint("ck_users_email_not_blank", "length(trim(email)) > 0")
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)
