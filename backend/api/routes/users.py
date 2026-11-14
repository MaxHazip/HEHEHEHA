"""Пользователи: инженеры для назначения на заявки."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, Field
from pwdlib import PasswordHash

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.access import COOKIE, SESSION_SECONDS, CurrentUser, allowed_origin, issue_session, require_staff
from backend.core.settings import settings
from backend.api.serializers import user_read
from backend.core.database import get_session
from backend.models import Engineer, User
from backend.schemas.ticket_schemas import UserRead
from backend.services.accounts import get_user_by_phone

router = APIRouter(prefix="/api/users", tags=["users"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[UserRead], summary="Список пользователей")
async def list_users(
    session: SessionDep,
    user: CurrentUser,
    role: str | None = None,
) -> list[UserRead]:
    require_staff(user)
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
async def login(payload: LoginRequest, session: SessionDep, request: Request, response: Response) -> UserRead:
    origin = request.headers.get("origin")
    if origin and not allowed_origin(origin, request.headers.get("host", "")):
        raise HTTPException(status_code=403, detail="Недопустимый источник запроса")
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
    response.set_cookie(
        COOKIE, issue_session(user), max_age=SESSION_SECONDS, httponly=True,
        secure=settings.SESSION_COOKIE_SECURE, samesite="strict",
    )
    return user_read(user, engineer_id=engineer_id)


@router.post("/logout", status_code=204)
async def logout(response: Response, _user: CurrentUser) -> None:
    response.delete_cookie(COOKIE)


@router.get("/me", response_model=UserRead)
async def me(session: SessionDep, user: CurrentUser) -> UserRead:
    profile = await session.scalar(select(Engineer.id).where(Engineer.user_id == user.id))
    return user_read(user, engineer_id=profile)
