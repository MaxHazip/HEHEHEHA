"""Browser sessions and access rules shared by HTTP and WebSocket routes."""

import hashlib
import hmac
import re
import secrets
import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_session
from backend.core.settings import settings
from backend.models import Call, ChatMessage, Engineer, Ticket, TicketAttachment, User

COOKIE = "dispatchai_session"
SESSION_SECONDS = 8 * 3600
SECRET = (settings.SESSION_SECRET or secrets.token_hex(32)).encode()
STAFF = {"dispatcher", "admin"}
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def issue_session(user: User) -> str:
    payload = f"{user.id}.{int(time.time()) + SESSION_SECONDS}"
    return f"{payload}.{_signature(payload)}"


def _signature(payload: str) -> str:
    return hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()


async def authenticated_user(session: AsyncSession, token: str | None) -> User:
    match = re.fullmatch(r"(\d{1,19})\.(\d{1,12})\.([a-f0-9]{64})", token or "")
    if match:
        user_id, expiry, signature = match.groups()
        if int(user_id) < 2**63 and int(expiry) > time.time() and hmac.compare_digest(
            signature, _signature(f"{user_id}.{expiry}")
        ):
            user = await session.get(User, int(user_id))
            if user is not None and user.is_active:
                return user
    raise HTTPException(status_code=401, detail="Войдите в систему")


def allowed_origin(origin: str, host: str) -> bool:
    return (
        origin in {f"http://{host}", f"https://{host}", *settings.cors_origins}
        or bool(settings.CORS_ORIGIN_REGEX and re.fullmatch(settings.CORS_ORIGIN_REGEX, origin))
    )


async def current_user(request: Request, session: SessionDep) -> User:
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
        if not allowed_origin(origin, request.headers.get("host", "")):
            raise HTTPException(status_code=403, detail="Недопустимый источник запроса")
    return await authenticated_user(session, request.cookies.get(COOKIE))


CurrentUser = Annotated[User, Depends(current_user)]


async def engineer_id(session: AsyncSession, user: User) -> int | None:
    return await session.scalar(select(Engineer.id).where(Engineer.user_id == user.id))


async def can_read_ticket(session: AsyncSession, user: User, ticket: Ticket) -> bool:
    if user.role in STAFF:
        return True
    if user.role == "requester":
        return ticket.created_by == user.id
    if user.role == "engineer" and ticket.engineer_id is not None:
        return ticket.engineer_id == await engineer_id(session, user)
    return False


async def require_ticket(session: AsyncSession, user: User, ticket_id: int) -> Ticket:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None or not await can_read_ticket(session, user, ticket):
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return ticket


async def can_read_call(session: AsyncSession, user: User, call: Call) -> bool:
    if user.role in STAFF or call.created_by == user.id:
        return True
    if call.ticket_id is None:
        return False
    ticket = await session.get(Ticket, call.ticket_id)
    return ticket is not None and await can_read_ticket(session, user, ticket)


def resource_id(value: str) -> int:
    if not re.fullmatch(r"[0-9]{1,19}", value) or not 0 < int(value) < 2**63:
        raise HTTPException(status_code=422, detail="Недопустимый идентификатор")
    return int(value)


async def protect_resources(request: Request, session: SessionDep, user: CurrentUser) -> None:
    params = request.path_params
    if "ticket_id" in params:
        await require_ticket(session, user, resource_id(params["ticket_id"]))
    if "call_id" in params:
        call = await session.get(Call, resource_id(params["call_id"]))
        if call is None or not await can_read_call(session, user, call):
            raise HTTPException(status_code=404, detail="Звонок не найден")
    if "attachment_id" in params:
        attachment = await session.get(TicketAttachment, resource_id(params["attachment_id"]))
        if attachment is None:
            raise HTTPException(status_code=404, detail="Вложение не найдено")
        ticket_id = attachment.ticket_id
        if ticket_id is None and attachment.message_id is not None:
            ticket_id = await session.scalar(
                select(Ticket.id).join(ChatMessage, ChatMessage.session_id == Ticket.chat_session_id)
                .where(ChatMessage.id == attachment.message_id)
            )
        if ticket_id is None:
            require_staff(user)
        else:
            await require_ticket(session, user, ticket_id)


def require_staff(user: User) -> None:
    if user.role not in STAFF:
        raise HTTPException(status_code=403, detail="Действие доступно диспетчеру")
