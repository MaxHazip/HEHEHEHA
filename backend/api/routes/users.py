"""Пользователи: инженеры для назначения на заявки."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.serializers import user_read
from backend.core.database import get_session
from backend.models import Engineer, User
from backend.schemas.ticket_schemas import UserRead

router = APIRouter(prefix="/api/users", tags=["users"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[UserRead], summary="Список пользователей")
async def list_users(
    session: SessionDep,
    role: str | None = None,
) -> list[UserRead]:
    stmt = select(User).where(User.is_active.is_(True))
    if role:
        stmt = stmt.where(User.role == role)
    stmt = stmt.order_by(User.id)

    users = (await session.scalars(stmt)).all()

    result: list[UserRead] = []
    for user in users:
        specialty = None
        engineer_id = None
        if user.role == "engineer":
            engineer = await session.scalar(
                select(Engineer).where(Engineer.user_id == user.id)
            )
            if engineer is not None:
                engineer_id = engineer.id
                if engineer.competencies:
                    specialty = engineer.competencies[0]
        read = user_read(user, specialty, engineer_id)
        if read is not None:
            result.append(read)
    return result
