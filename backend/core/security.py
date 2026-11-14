"""Хеширование паролей и выпуск JWT access-токенов."""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from backend.core.settings import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    try:
        return password_hash.verify(password, hashed_password)
    except (ValueError, TypeError):
        return False


def create_access_token(*, user_id: int, role: str) -> str:
    if (
        not settings.JWT_SECRET_KEY
        or settings.JWT_SECRET_KEY == "CHANGE_ME_USE_A_LONG_RANDOM_SECRET_IN_ENV"
        or len(settings.JWT_SECRET_KEY) < 32
    ):
        raise RuntimeError(
            "JWT_SECRET_KEY не настроен. Укажите случайный секрет длиной не менее 32 символов."
        )

    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expires,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    if (
        not settings.JWT_SECRET_KEY
        or settings.JWT_SECRET_KEY == "CHANGE_ME_USE_A_LONG_RANDOM_SECRET_IN_ENV"
        or len(settings.JWT_SECRET_KEY) < 32
    ):
        raise RuntimeError(
            "JWT_SECRET_KEY не настроен. Укажите случайный секрет длиной не менее 32 символов."
        )
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat"]},
    )
