"""Funciones criptográficas para autenticación y control de acceso."""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.shared.settings import settings

_password_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=4)


def hash_password(plain_password: str) -> str:
    """Hashea contraseñas utilizando Argon2id."""

    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Valida una contraseña utilizando Argon2id."""

    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_jwt(payload: Dict[str, Any], expires_delta: dt.timedelta | None = None) -> str:
    """Genera un JWT firmado con HS256."""

    now = dt.datetime.utcnow()
    if expires_delta is None:
        expires_delta = dt.timedelta(minutes=settings.access_token_exp_minutes)
    exp = now + expires_delta
    payload = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_jwt(token: str) -> Dict[str, Any]:
    """Decodifica un token JWT y retorna el payload."""

    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
