"""Скачивание и описание вложений."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai_module.services.image_service import describe_attachment
from backend.api.serializers import attachment_read
from backend.core.database import get_session
from backend.models import TicketAttachment
from backend.schemas.ticket_schemas import AttachmentRead
from backend.services.storage import file_response


router = APIRouter(prefix="/api/attachments", tags=["attachments"])

from backend.api.dependencies import get_current_user

router = APIRouter(prefix="/api/attachments", tags=["attachments"], dependencies=[Depends(get_current_user)])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _get_or_404(
    session: AsyncSession, attachment_id: int
) -> TicketAttachment:
    attachment = await session.get(TicketAttachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Вложение не найдено")
    return attachment


@router.get(
    "/{attachment_id}",
    response_model=AttachmentRead,
    summary="Метаданные вложения",
)
async def read_attachment(
    attachment_id: int, session: SessionDep
) -> AttachmentRead:
    attachment = await _get_or_404(session, attachment_id)
    return attachment_read(attachment)


@router.get(
    "/{attachment_id}/content",
    summary="Содержимое вложения (картинка/файл)",
)
async def download_attachment(
    attachment_id: int,
    request: Request,
    session: SessionDep,
) -> Response:
    attachment = await _get_or_404(session, attachment_id)

    if attachment.data is None:
        raise HTTPException(
            status_code=404,
            detail="Файл хранится вне БД и недоступен по этому адресу",
        )


    return file_response(
        request,
        attachment.data,
        attachment.mime_type,

        attachment.file_name,

        attachment.filename,

    )


@router.post(
    "/{attachment_id}/describe",
    response_model=AttachmentRead,

    summary="Описать изображение локальной vision-моделью (Qwen3-VL)",

    summary="Описать изображение с помощью Gemini",

)
async def describe_image(
    attachment_id: int, session: SessionDep
) -> AttachmentRead:
    attachment = await _get_or_404(session, attachment_id)

    if attachment.kind != "image":
        raise HTTPException(
            status_code=422, detail="Описать можно только изображение"
        )

    if attachment.data is None:
        raise HTTPException(
            status_code=422, detail="Изображение не хранится в БД"
        )



    description = await describe_attachment(
        attachment.data, attachment.mime_type
    )
    if not description:
        raise HTTPException(
            status_code=503,
            detail=(

                "Vision-модель не настроена. Задайте VISION_PROVIDER=ollama "
                "и OLLAMA_VISION_MODEL (например, qwen3-vl:2b) или ключ Gemini."
            ),
        )

    attachment.description = description
    await session.commit()
    await session.refresh(attachment)
    return attachment_read(attachment)


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить вложение",
)
async def delete_attachment(
    attachment_id: int, session: SessionDep
) -> Response:
    attachment = await _get_or_404(session, attachment_id)
    await session.delete(attachment)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
