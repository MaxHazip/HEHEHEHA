"""Пользователи: инженеры для назначения на заявки."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.serializers import user_read
from backend.core.database import get_session
from backend.models import User
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
    return [user_read(user) for user in users if user_read(user) is not None]
