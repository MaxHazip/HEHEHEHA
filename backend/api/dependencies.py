"""Общие зависимости авторизации и проверки ролей."""

from collections.abc import Callable
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status, WebSocketException
from starlette.requests import HTTPConnection
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_session
from backend.core.security import decode_access_token
from backend.models import User


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    connection: HTTPConnection,
    session: SessionDep,
) -> User:
    authorization = connection.headers.get("Authorization", "")
    token = None
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    # Для WebSocket браузер не позволяет задать Authorization header.
    if not token and connection.scope["type"] == "websocket":
        token = connection.query_params.get("access_token")

    if not token:
        if connection.scope["type"] == "websocket":
            raise WebSocketException(code=1008, reason="Требуется авторизация")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        user_id = int(payload["sub"])
    except RuntimeError as exc:
        if connection.scope["type"] == "websocket":
            raise WebSocketException(code=1011, reason="JWT_SECRET_KEY не настроен")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        if connection.scope["type"] == "websocket":
            raise WebSocketException(code=1008, reason="Недействительный токен")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        if connection.scope["type"] == "websocket":
            raise WebSocketException(code=1008, reason="Пользователь неактивен")
        raise HTTPException(status_code=401, detail="Пользователь не найден или отключён")
    return user


def require_roles(*allowed_roles: str) -> Callable:
    async def role_dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции",
            )
        return user

    return role_dependency
