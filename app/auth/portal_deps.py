"""Shared dependencies for authenticated portal users."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.security.deps import get_auth_context
from app.security.policies import AuthContext


def get_authenticated_user(
    context: AuthContext = Depends(get_auth_context),
) -> tuple[User, dict]:
    if context.user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return context.user, context.token_payload
