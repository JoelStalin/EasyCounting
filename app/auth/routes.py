"""Rutas de autenticación."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.auth.deps import get_service
from app.auth.schemas import LoginRequest, LoginResponse, MFARequest, UserRead
from app.auth.service import AuthService
from app.models.user import User
from app.shared.security import decode_jwt

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, service: AuthService = Depends(get_service)) -> LoginResponse:
    """Realiza autenticación tradicional (primer factor)."""

    _, tokens = service.authenticate(payload.email, payload.password)
    return tokens


@router.post("/mfa/verify", response_model=dict[str, bool])
async def verify_mfa(payload: MFARequest, service: AuthService = Depends(get_service)) -> dict[str, bool]:
    """Valida códigos TOTP enviados por el usuario."""

    return {"valid": service.verify_mfa(payload.email, payload.code)}


@router.get("/me", response_model=UserRead)
async def me(
    authorization: str = Header(..., alias="Authorization"),
    service: AuthService = Depends(get_service),
) -> UserRead:
    """Retorna información del usuario autenticado."""

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization inválido")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_jwt(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin sujeto")
    try:
        user_pk = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc

    user = service.repository.db.get(User, user_pk)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UserRead.model_validate(user, from_attributes=True)
