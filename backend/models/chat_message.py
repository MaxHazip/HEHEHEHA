from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base  

if TYPE_CHECKING:
    from backend.models.chat_session import ChatSession


class ChatMessageRoles(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    __table_args__ = (
        CheckConstraint(
            "btrim(content) <> ''",
            name="ck_chat_messages_content_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    session_id: Mapped[PG_UUID] = mapped_column(  
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,                   
    )

    role: Mapped[ChatMessageRoles] = mapped_column(
        Enum(
            ChatMessageRoles,
            name="chat_message_role_enum",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(  
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )