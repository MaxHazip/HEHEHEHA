"""Экспорт ORM-моделей.

Alembic и приложение импортируют этот модуль целиком, чтобы все модели
были зарегистрированы в ``Base.metadata``.
"""

from backend.models.call import Call, CallTranscriptSegment
from backend.models.category import Category
from backend.models.chat_message import ChatMessage
from backend.models.chat_session import ChatSession
from backend.models.engineer import Engineer
from backend.models.knowledge_article_models import KnowledgeArticle
from backend.models.subcategory import Subcategory
from backend.models.ticket import Ticket
from backend.models.ticket_analysis import TicketAnalysis
from backend.models.ticket_attachment import TicketAttachment
from backend.models.ticket_event import TicketEvent
from backend.models.ticket_kb_article_models import TicketKBArticle
from backend.models.user import User

__all__ = [
    "Call",
    "CallTranscriptSegment",
    "Category",
    "ChatMessage",
    "ChatSession",
    "Engineer",
    "KnowledgeArticle",
    "Subcategory",
    "Ticket",
    "TicketAnalysis",
    "TicketAttachment",
    "TicketEvent",
    "TicketKBArticle",
    "User",
]
