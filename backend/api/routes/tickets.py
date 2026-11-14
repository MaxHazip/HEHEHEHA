"""Заявки, сообщения и вложения к заявкам."""

import hashlib
import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from ai_module.core.schemas import TicketAIResult
from backend.api.serializers import (
    attachment_read,

    build_ticket_detail,
    build_ticket_summary,
    call_summary,
    message_read,
)
from backend.core.database import get_session
from backend.core.settings import settings
from backend.models import (
    Call,
    ChatMessage,
    ChatSession,
    Engineer,
    Ticket,
    TicketAttachment,
)

   ( call_summary,
    message_read,
    ticket_detail,
    ticket_summary,
)
from backend.core.database import get_session
from backend.core.settings import settings
from backend.models import Call, Ticket, TicketAttachment, TicketMessage, User

from backend.schemas.ai_schemas import AnalyzeTicketRequest
from backend.schemas.ticket_schemas import (
    AttachmentRead,
    CallSummary,
    MessageCreate,
    MessageRead,
    TicketAssign,
    TicketCreate,
    TicketDetail,
    TicketSummary,
    TicketUpdate,

    normalize_role,
)
from backend.services.accounts import get_or_create_requester

)

from backend.services.ai_service import analyze_ticket
from backend.services.storage import (
    UploadTooLargeError,
    detect_kind,
    guess_mime,
    read_upload,
    safe_filename,
)


router = APIRouter(prefix="/api/tickets", tags=["tickets"])

from backend.api.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api/tickets", tags=["tickets"], dependencies=[Depends(get_current_user)])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
logger = logging.getLogger(__name__)


async def get_ticket_or_404(session: AsyncSession, ticket_id: int) -> Ticket:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return ticket



async def _session_messages(
    session: AsyncSession, ticket: Ticket
) -> list[ChatMessage]:
    rows = (
        await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == ticket.chat_session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        )
    ).all()
    return list(rows)

async def _assignee(session: AsyncSession, ticket: Ticket) -> User | None:
    if ticket.assignee_id is None:
        return None
    return await session.get(User, ticket.assignee_id)


async def _build_detail(session: AsyncSession, ticket: Ticket) -> TicketDetail:
    assignee = await _assignee(session, ticket)

    messages = (
        await session.scalars(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.id)
        )
    ).all()

    attachments = (
        await session.scalars(
            select(TicketAttachment)
            .options(defer(TicketAttachment.data))
            .where(TicketAttachment.ticket_id == ticket.id)
            .order_by(TicketAttachment.id)
        )
    ).all()
    attachment_reads = [attachment_read(item) for item in attachments]

    by_message: dict[int, list[AttachmentRead]] = {}
    for item in attachment_reads:
        if item.message_id is not None:
            by_message.setdefault(item.message_id, []).append(item)

    message_reads = [
        message_read(message, by_message.get(message.id))
        for message in messages
    ]

    calls = (
        await session.scalars(
            select(Call)
            .options(defer(Call.recording_data))
            .where(Call.ticket_id == ticket.id)
            .order_by(Call.id)
        )
    ).all()

    return ticket_detail(
        ticket,
        assignee,
        message_reads,
        attachment_reads,
        [call_summary(call) for call in calls],
    )



@router.post(
    "",
    response_model=TicketDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заявку",
)
async def create_ticket(
    payload: TicketCreate,
    session: SessionDep,
) -> TicketDetail:

    text = (payload.description or payload.title or "").strip()
    if not text:

    if not payload.title and not payload.description.strip():

        raise HTTPException(
            status_code=422,
            detail="Нужен заголовок или описание обращения",
        )


    requester = await get_or_create_requester(session)

    chat_session = ChatSession(user_id=requester.id, status="active")
    session.add(chat_session)
    await session.flush()

    session.add(
        ChatMessage(
            session_id=chat_session.id,
            role="user",
            content=text,
        )
    )

    ticket = Ticket(
        chat_session_id=chat_session.id,
        created_by=requester.id,
        raw_text=text,
        channel="voice" if payload.source == "phone" else "chat",
        status="draft",
        priority=payload.priority,
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    if settings.AI_AUTO_ANALYZE:

    title = (payload.title or payload.description.strip()[:60]).strip()
    ticket = Ticket(
        title=title[:255] or "Новое обращение",
        description=payload.description.strip(),
        source=payload.source,
        priority=payload.priority,
        client_name=payload.client_name,
        client_phone=payload.client_phone,
    )
    session.add(ticket)
    await session.flush()

    if payload.description.strip():
        session.add(
            TicketMessage(
                ticket_id=ticket.id,
                role="client",
                text=payload.description.strip(),
            )
        )

    await session.commit()
    await session.refresh(ticket)

    if settings.AI_AUTO_ANALYZE and payload.description.strip():

        try:
            await analyze_ticket(session, ticket, force=True)
        except Exception:  # noqa: BLE001
            # Заявка уже создана; сбой ИИ не должен ломать приём обращения.
            logger.exception(
                "Автоматический ИИ-анализ не удался для заявки %s", ticket.id
            )


    return await build_ticket_detail(session, ticket)

    return await _build_detail(session, ticket)



@router.get(
    "",
    response_model=list[TicketSummary],
    summary="Список заявок",
)
async def list_tickets(
    session: SessionDep,
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    assignee_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[TicketSummary]:
    stmt = select(Ticket)

    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if assignee_id is not None:

        stmt = stmt.where(Ticket.engineer_id == assignee_id)

    stmt = (
        stmt.order_by(Ticket.created_at.desc())
        .limit(min(limit, 200))
        .offset(offset)
    )
    tickets = (await session.scalars(stmt)).all()

    return [
        await build_ticket_summary(session, ticket) for ticket in tickets

        stmt = stmt.where(Ticket.assignee_id == assignee_id)

    stmt = stmt.order_by(Ticket.created_at.desc()).limit(min(limit, 200)).offset(offset)
    tickets = (await session.scalars(stmt)).all()

    assignee_ids = {
        ticket.assignee_id for ticket in tickets if ticket.assignee_id is not None
    }
    assignees: dict[int, User] = {}
    if assignee_ids:
        users = (
            await session.scalars(select(User).where(User.id.in_(assignee_ids)))
        ).all()
        assignees = {user.id: user for user in users}

    return [
        ticket_summary(
            ticket,
            assignees.get(ticket.assignee_id) if ticket.assignee_id else None,
        )
        for ticket in tickets

    ]


@router.get(
    "/{ticket_id}",
    response_model=TicketDetail,
    summary="Заявка с сообщениями, вложениями и звонками",
)
async def read_ticket(ticket_id: int, session: SessionDep) -> TicketDetail:
    ticket = await get_ticket_or_404(session, ticket_id)

    return await build_ticket_detail(session, ticket)

    return await _build_detail(session, ticket)



@router.patch(
    "/{ticket_id}",
    response_model=TicketDetail,
    summary="Обновить заявку",


    dependencies=[Depends(require_roles("admin", "dispatcher"))],

)
async def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    session: SessionDep,
) -> TicketDetail:
    ticket = await get_ticket_or_404(session, ticket_id)
    data = payload.model_dump(exclude_unset=True)


    if data.get("engineer_id") is not None:
        engineer = await session.get(Engineer, data["engineer_id"])
        if engineer is None:
            raise HTTPException(status_code=404, detail="Инженер не найден")

    if "assignee_id" in data and data["assignee_id"] is not None:
        user = await session.get(User, data["assignee_id"])
        if user is None:
            raise HTTPException(status_code=404, detail="Исполнитель не найден")


    for field, value in data.items():
        setattr(ticket, field, value)

    await session.commit()
    await session.refresh(ticket)

    return await build_ticket_detail(session, ticket)

    return await _build_detail(session, ticket)



@router.post(
    "/{ticket_id}/assign",
    response_model=TicketDetail,

    summary="Назначить инженера",

    summary="Назначить исполнителя",
    dependencies=[Depends(require_roles("admin", "dispatcher"))],

)
async def assign_ticket(
    ticket_id: int,
    payload: TicketAssign,
    session: SessionDep,
) -> TicketDetail:
    ticket = await get_ticket_or_404(session, ticket_id)

    engineer = await session.get(Engineer, payload.engineer_id)
    if engineer is None:
        raise HTTPException(status_code=404, detail="Инженер не найден")
    ticket.engineer_id = engineer.id
    await session.commit()
    await session.refresh(ticket)
    return await build_ticket_detail(session, ticket)

    user = await session.get(User, payload.assignee_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Исполнитель не найден")
    ticket.assignee_id = user.id
    await session.commit()
    await session.refresh(ticket)
    return await _build_detail(session, ticket)



@router.get(
    "/{ticket_id}/messages",
    response_model=list[MessageRead],
    summary="Сообщения заявки",
)
async def list_messages(
    ticket_id: int, session: SessionDep
) -> list[MessageRead]:
    ticket = await get_ticket_or_404(session, ticket_id)


    messages = await _session_messages(session, ticket)

    messages = (
        await session.scalars(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.id)
        )
    ).all()

    attachments = (
        await session.scalars(
            select(TicketAttachment)
            .options(defer(TicketAttachment.data))
            .where(TicketAttachment.ticket_id == ticket.id)
        )
    ).all()

    by_message: dict[int, list[AttachmentRead]] = {}
    for item in attachments:
        if item.message_id is not None:
            by_message.setdefault(item.message_id, []).append(
                attachment_read(item)
            )

    return [

        message_read(message, ticket.id, by_message.get(message.id))

        message_read(message, by_message.get(message.id))

        for message in messages
    ]


@router.post(
    "/{ticket_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить сообщение",
)
async def add_message(
    ticket_id: int,
    payload: MessageCreate,
    session: SessionDep,
    analyze: bool = False,
) -> MessageRead:
    ticket = await get_ticket_or_404(session, ticket_id)


    text = payload.text.strip()
    if not text and not payload.attachment_ids:
        raise HTTPException(status_code=422, detail="Сообщение пустое")

    message = ChatMessage(
        session_id=ticket.chat_session_id,
        role=normalize_role(payload.role),
        # content не может быть пустым: для сообщения-только-с-файлом
        # подставляем служебную подпись.
        content=text or "[вложение]",

    if not payload.text.strip() and not payload.attachment_ids:
        raise HTTPException(status_code=422, detail="Сообщение пустое")

    message = TicketMessage(
        ticket_id=ticket.id,
        role=payload.role,
        text=payload.text.strip(),

    )
    session.add(message)
    await session.flush()

    attachments: list[TicketAttachment] = []
    if payload.attachment_ids:
        rows = (
            await session.scalars(
                select(TicketAttachment)
                .options(defer(TicketAttachment.data))
                .where(
                    TicketAttachment.id.in_(payload.attachment_ids),
                    TicketAttachment.ticket_id == ticket.id,
                )
            )
        ).all()
        found = {row.id for row in rows}
        missing = set(payload.attachment_ids) - found
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Вложения не найдены: {sorted(missing)}",
            )
        for row in rows:
            row.message_id = message.id

            row.ticket_id = ticket.id


            attachments.append(row)

    await session.commit()
    await session.refresh(message)


    if analyze and message.role == "user":

    if analyze and payload.role == "client":

        try:
            await analyze_ticket(session, ticket, force=True)
        except Exception:  # noqa: BLE001
            logger.exception(
                "ИИ-анализ после сообщения не удался для заявки %s", ticket.id
            )

    return message_read(

        message, ticket.id, [attachment_read(item) for item in attachments]

        message, [attachment_read(item) for item in attachments]

    )


@router.get(
    "/{ticket_id}/attachments",
    response_model=list[AttachmentRead],
    summary="Вложения заявки (без содержимого)",
)
async def list_attachments(
    ticket_id: int, session: SessionDep
) -> list[AttachmentRead]:
    ticket = await get_ticket_or_404(session, ticket_id)
    rows = (
        await session.scalars(
            select(TicketAttachment)
            .options(defer(TicketAttachment.data))
            .where(TicketAttachment.ticket_id == ticket.id)
            .order_by(TicketAttachment.id)
        )
    ).all()
    return [attachment_read(row) for row in rows]


@router.post(
    "/{ticket_id}/attachments",
    response_model=AttachmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить вложение (фото/аудио/документ)",
)
async def upload_attachment(
    ticket_id: int,
    session: SessionDep,
    file: Annotated[UploadFile, File(description="Файл")],
    kind: Annotated[str | None, Form()] = None,
    message_id: Annotated[int | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
) -> AttachmentRead:
    ticket = await get_ticket_or_404(session, ticket_id)

    if message_id is not None:

        message = await session.get(ChatMessage, message_id)
        if (
            message is None
            or message.session_id != ticket.chat_session_id
        ):

        message = await session.get(TicketMessage, message_id)
        if message is None or message.ticket_id != ticket.id:

            raise HTTPException(
                status_code=404, detail="Сообщение не найдено в этой заявке"
            )

    try:
        data = await read_upload(file, settings.max_upload_bytes)
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = safe_filename(file.filename)
    mime_type = guess_mime(filename, file.content_type)

    attachment_kind = (
        kind
        if kind in ("image", "audio", "document")
        else detect_kind(mime_type, filename)

    attachment_kind = kind if kind in ("image", "audio", "document") else detect_kind(
        mime_type, filename

    )

    attachment = TicketAttachment(
        ticket_id=ticket.id,
        message_id=message_id,
        kind=attachment_kind,

        file_name=filename,
        storage_path=f"db://tickets/{ticket.id}/{filename}",
        mime_type=mime_type,
        file_size=len(data),

        filename=filename,
        mime_type=mime_type,
        size_bytes=len(data),

        sha256=hashlib.sha256(data).hexdigest(),
        data=data,
        description=description,
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)

    return attachment_read(attachment)


@router.get(
    "/{ticket_id}/calls",
    response_model=list[CallSummary],
    summary="Звонки по заявке",
)
async def list_ticket_calls(
    ticket_id: int, session: SessionDep
) -> list[CallSummary]:
    ticket = await get_ticket_or_404(session, ticket_id)
    calls = (
        await session.scalars(
            select(Call)
            .options(defer(Call.recording_data))
            .where(Call.ticket_id == ticket.id)
            .order_by(Call.id)
        )
    ).all()
    return [call_summary(call) for call in calls]


@router.post(
    "/{ticket_id}/analyze",
    response_model=TicketAIResult,
    summary="Запустить ИИ-анализ заявки",
)
async def analyze_ticket_endpoint(
    ticket_id: int,
    session: SessionDep,
    payload: AnalyzeTicketRequest | None = None,
) -> TicketAIResult:
    ticket = await get_ticket_or_404(session, ticket_id)
    force = payload.force if payload else True
    return await analyze_ticket(session, ticket, force=force)
