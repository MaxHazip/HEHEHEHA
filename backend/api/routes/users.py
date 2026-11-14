"""Пользователи: инженеры для назначения на заявки."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pwdlib import PasswordHash

from backend.services.accounts import get_user_by_phone
import re
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


class LoginRequest(BaseModel):
    phone: str = Field(max_length=40)
    password: str = Field(min_length=1, max_length=256)


@router.post("/login", response_model=UserRead)
async def login(payload: LoginRequest, session: SessionDep) -> UserRead:
    digits = re.sub(r"[^0-9]", "", payload.phone)
    if len(digits) == 10:
        digits = "7" + digits
    elif len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    user = await get_user_by_phone(session, "+" + digits)
    if user is None or not user.is_active or not PasswordHash.recommended().verify(
        payload.password, user.password_hash
    ):
        raise HTTPException(status_code=401, detail="Неверный телефон или пароль")
    engineer_id = await session.scalar(select(Engineer.id).where(Engineer.user_id == user.id))
    return user_read(user, engineer_id=engineer_id)
