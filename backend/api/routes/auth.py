"""Регистрация, вход и получение профиля текущего пользователя."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.core.database import get_session
from backend.core.security import create_access_token, hash_password, verify_password
from backend.core.settings import settings
from backend.models import User
from backend.schemas.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: SessionDep) -> TokenResponse:
    """Самостоятельная регистрация доступна только заявителям.

    Роль не принимается из запроса: это не позволяет повысить собственные права.
    Сотрудников создаёт администратор отдельным административным процессом.
    """
    phone = payload.phone.strip()
    name = payload.name.strip()
    if len(name) < 2 or not phone:
        raise HTTPException(status_code=422, detail="Укажите корректные имя и телефон")
    existing = await session.scalar(select(User).where(User.phone == phone))
    if existing:
        raise HTTPException(status_code=409, detail="Пользователь с таким телефоном уже существует")

    user = User(
        name=name,
        phone=phone,
        role="client",
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    session.add(user)
    await session.flush()
    try:
        token = create_access_token(user_id=user.id, role=user.role)
    except RuntimeError as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    await session.commit()
    await session.refresh(user)
    return TokenResponse(
        access_token=token,
        expires_in=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserProfile.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    phone = payload.phone.strip()
    user = await session.scalar(select(User).where(User.phone == phone))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный номер телефона или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = create_access_token(user_id=user.id, role=user.role)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return TokenResponse(
        access_token=token,
        expires_in=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserProfile.model_validate(user),
    )


@router.get("/me", response_model=UserProfile)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserProfile:
    return UserProfile.model_validate(user)
