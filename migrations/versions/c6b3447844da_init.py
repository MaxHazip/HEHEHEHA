"""init: полная схема DispatchAI

Revision ID: c6b3447844da
Revises:
Create Date: 2026-11-14

Миграция написана кросс-диалектно: в PostgreSQL создаются ``BIGINT``,
``TEXT[]``, ``JSONB`` и ``TIMESTAMPTZ``, в SQLite — их эквиваленты.
Это позволяет прогнать ``alembic upgrade head`` и на локальном SQLite,
и на PostgreSQL из ``docker-compose``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c6b3447844da"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _bigint():
    return sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def _text_array():
    return postgresql.ARRAY(sa.Text()).with_variant(sa.JSON(), "sqlite")


def _jsonb():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(
        sa.JSON(), "sqlite"
    )


def _uuid():
    return sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('requester', 'dispatcher', 'engineer')",
            name="ck_users_role",
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_users_name_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(email)) > 0",
            name="ck_users_email_not_blank",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_users_email_lower",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )

    op.create_table(
        "categories",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.CheckConstraint(
            "length(trim(code)) > 0",
            name="ck_categories_code_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_categories_name_not_blank",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "knowledge_articles",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("keywords", _text_array(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(code)) > 0",
            name="ck_knowledge_articles_code_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(title)) > 0",
            name="ck_knowledge_articles_title_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(body)) > 0",
            name="ck_knowledge_articles_body_not_blank",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("user_id", _bigint(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'cancelled')",
            name="ck_chat_sessions_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_sessions_user_id", "chat_sessions", ["user_id"], unique=False
    )

    op.create_table(
        "engineers",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("user_id", _bigint(), nullable=False),
        sa.Column("competencies", _text_array(), nullable=False),
        sa.Column("load", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "available",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.CheckConstraint("load >= 0", name="ck_engineers_load_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "subcategories",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("category_id", _bigint(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.CheckConstraint(
            "length(trim(code)) > 0",
            name="ck_subcategories_code_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_subcategories_name_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "category_id", "code", name="uq_subcategories_category_code"
        ),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("session_id", _uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_chat_messages_role",
        ),
        sa.CheckConstraint(
            "trim(content) <> ''",
            name="ck_chat_messages_content_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_messages_session_id",
        "chat_messages",
        ["session_id"],
        unique=False,
    )

    op.create_table(
        "tickets",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("chat_session_id", _uuid(), nullable=False),
        sa.Column("created_by", _bigint(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("category_id", _bigint(), nullable=True),
        sa.Column("subcategory_id", _bigint(), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("device", sa.String(length=100), nullable=True),
        sa.Column("building", sa.String(length=100), nullable=True),
        sa.Column("floor", sa.String(length=30), nullable=True),
        sa.Column("room", sa.String(length=50), nullable=True),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("symptoms", _text_array(), nullable=False),
        sa.Column("attempted_actions", _text_array(), nullable=False),
        sa.Column("missing_fields", _text_array(), nullable=False),
        sa.Column(
            "is_mass_incident",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "needs_human_review",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column("recommended_engineer_id", _bigint(), nullable=True),
        sa.Column("engineer_id", _bigint(), nullable=True),
        sa.Column("confirmed_by", _bigint(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'new', 'in_progress', 'resolved', 'closed')",
            name="ck_tickets_status",
        ),
        sa.CheckConstraint(
            "priority IS NULL OR priority IN "
            "('low', 'medium', 'high', 'critical')",
            name="ck_tickets_priority",
        ),
        sa.CheckConstraint(
            "channel IN ('chat', 'voice', 'image')",
            name="ck_tickets_channel",
        ),
        sa.CheckConstraint(
            "length(trim(raw_text)) > 0",
            name="ck_tickets_raw_text_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["chat_session_id"], ["chat_sessions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["engineer_id"], ["engineers.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["recommended_engineer_id"], ["engineers.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["subcategory_id"], ["subcategories.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_session_id"),
    )
    op.create_index(
        "ix_tickets_created_by", "tickets", ["created_by"], unique=False
    )
    op.create_index(
        "ix_tickets_engineer_id", "tickets", ["engineer_id"], unique=False
    )
    op.create_index("ix_tickets_status", "tickets", ["status"], unique=False)

    op.create_table(
        "ticket_analyses",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("chat_session_id", _uuid(), nullable=False),
        sa.Column("ticket_id", _bigint(), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("result", _jsonb(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("version >= 1", name="ck_ticket_analyses_version"),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_ticket_analyses_confidence",
        ),
        sa.ForeignKeyConstraint(
            ["chat_session_id"], ["chat_sessions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"], ["tickets.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chat_session_id",
            "version",
            name="uq_ticket_analyses_session_version",
        ),
    )
    op.create_index(
        "ix_ticket_analyses_chat_session_id",
        "ticket_analyses",
        ["chat_session_id"],
        unique=False,
    )
    op.create_index(
        "ix_ticket_analyses_ticket_id",
        "ticket_analyses",
        ["ticket_id"],
        unique=False,
    )

    op.create_table(
        "ticket_attachments",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("message_id", _bigint(), nullable=True),
        sa.Column("ticket_id", _bigint(), nullable=True),
        sa.Column(
            "kind",
            sa.String(length=16),
            server_default=sa.text("'document'"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", _bigint(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("data", sa.LargeBinary(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('image', 'audio', 'document')",
            name="ck_ticket_attachments_kind",
        ),
        sa.CheckConstraint(
            "file_size > 0",
            name="ck_ticket_attachments_file_size",
        ),
        sa.CheckConstraint(
            "length(trim(file_name)) > 0",
            name="ck_ticket_attachments_file_name",
        ),
        sa.CheckConstraint(
            "length(trim(storage_path)) > 0",
            name="ck_ticket_attachments_storage_path",
        ),
        sa.CheckConstraint(
            "length(trim(mime_type)) > 0",
            name="ck_ticket_attachments_mime_type",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"], ["chat_messages.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"], ["tickets.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ticket_attachments_message_id",
        "ticket_attachments",
        ["message_id"],
        unique=False,
    )
    op.create_index(
        "ix_ticket_attachments_ticket_id",
        "ticket_attachments",
        ["ticket_id"],
        unique=False,
    )

    op.create_table(
        "ticket_events",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("ticket_id", _bigint(), nullable=False),
        sa.Column("actor_id", _bigint(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("field", sa.String(length=100), nullable=True),
        sa.Column("old_value", _jsonb(), nullable=True),
        sa.Column("new_value", _jsonb(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(action)) > 0",
            name="ck_ticket_events_action_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"], ["tickets.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ticket_events_actor_id", "ticket_events", ["actor_id"], unique=False
    )
    op.create_index(
        "ix_ticket_events_ticket_id", "ticket_events", ["ticket_id"], unique=False
    )

    op.create_table(
        "ticket_kb_articles",
        sa.Column("ticket_id", _bigint(), nullable=False),
        sa.Column("article_id", _bigint(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.CheckConstraint(
            "relevance_score IS NULL OR "
            "(relevance_score >= 0 AND relevance_score <= 1)",
            name="ck_ticket_kb_articles_relevance_score",
        ),
        sa.ForeignKeyConstraint(
            ["article_id"], ["knowledge_articles.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"], ["tickets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("ticket_id", "article_id"),
    )

    create_calls_table()
    create_transcript_table()


def create_calls_table() -> None:
    op.create_table(
        "calls",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("ticket_id", _bigint(), nullable=True),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column(
            "direction",
            sa.String(length=16),
            server_default=sa.text("'inbound'"),
            nullable=False,
        ),
        sa.Column(
            "transport",
            sa.String(length=16),
            server_default=sa.text("'webrtc'"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("client_phone", sa.String(length=32), nullable=True),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("recording_mime", sa.String(length=128), nullable=True),
        sa.Column("recording_size", sa.Integer(), nullable=True),
        sa.Column("recording_data", sa.LargeBinary(), nullable=True),
        sa.Column("recording_name", sa.String(length=128), nullable=True),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("transcript_language", sa.String(length=16), nullable=True),
        sa.Column("transcript_provider", sa.String(length=64), nullable=True),
        sa.Column("ai_analysis", _jsonb(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"], ["tickets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calls_ticket_id", "calls", ["ticket_id"], unique=False)
    op.create_index(
        "ix_calls_external_id", "calls", ["external_id"], unique=False
    )
    op.create_index("ix_calls_status", "calls", ["status"], unique=False)
    op.create_index(
        "ix_calls_recording_name", "calls", ["recording_name"], unique=False
    )
    op.create_index("ix_calls_created_at", "calls", ["created_at"], unique=False)



def create_transcript_table() -> None:
    op.create_table(
        "call_transcript_segments",
        sa.Column("id", _bigint(), autoincrement=True, nullable=False),
        sa.Column("call_id", _bigint(), nullable=False),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=True),
        sa.Column("end_ms", sa.Integer(), nullable=True),
        sa.Column("speaker", sa.String(length=20), nullable=True),
        sa.Column("text", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["call_id"], ["calls.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_call_transcript_segments_call_id",
        "call_transcript_segments",
        ["call_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_call_transcript_segments_call_id",
        table_name="call_transcript_segments",
    )
    op.drop_table("call_transcript_segments")

    op.drop_index("ix_calls_created_at", table_name="calls")
    op.drop_index("ix_calls_recording_name", table_name="calls")
    op.drop_index("ix_calls_status", table_name="calls")
    op.drop_index("ix_calls_external_id", table_name="calls")
    op.drop_index("ix_calls_ticket_id", table_name="calls")
    op.drop_table("calls")

    op.drop_table("ticket_kb_articles")

    op.drop_index("ix_ticket_events_ticket_id", table_name="ticket_events")
    op.drop_index("ix_ticket_events_actor_id", table_name="ticket_events")
    op.drop_table("ticket_events")

    op.drop_index(
        "ix_ticket_attachments_ticket_id", table_name="ticket_attachments"
    )
    op.drop_index(
        "ix_ticket_attachments_message_id", table_name="ticket_attachments"
    )
    op.drop_table("ticket_attachments")

    op.drop_index(
        "ix_ticket_analyses_ticket_id", table_name="ticket_analyses"
    )
    op.drop_index(
        "ix_ticket_analyses_chat_session_id", table_name="ticket_analyses"
    )
    op.drop_table("ticket_analyses")

    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_engineer_id", table_name="tickets")
    op.drop_index("ix_tickets_created_by", table_name="tickets")
    op.drop_table("tickets")

    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_table("subcategories")

    op.drop_table("engineers")

    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_table("knowledge_articles")
    op.drop_table("categories")

    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_table("users")
