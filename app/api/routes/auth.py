"""Authentication endpoints used by the client/admin portals."""
from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.auth.deps import get_service
from app.auth.service import AuthService
from app.infra.settings import settings
from app.models.user import User
from app.shared.security import create_jwt, decode_jwt

router = APIRouter()
me_router = APIRouter()


class _LoginPayload(BaseModel):
    email: str
    password: str = Field(min_length=8)


class _UserPayload(BaseModel):
    id: str
    email: EmailStr
    scope: Literal["PLATFORM", "TENANT", "PARTNER"]
    tenant_id: str | None
    roles: list[str]


class _LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: _UserPayload
    permissions: list[str]
    mfa_required: bool


class _MFAPayload(BaseModel):
    email: str
    code: str = Field(min_length=6, max_length=6)


class _AuthUser(BaseModel):
    id: str
    email: EmailStr
    scope: Literal["PLATFORM", "TENANT", "PARTNER"]
    tenantId: str | None
    roles: list[str]


class _AuthSession(BaseModel):
    accessToken: str
    refreshToken: str
    user: _AuthUser
    permissions: list[str]


def _is_platform_role(role: str) -> bool:
    return role.startswith("platform_")


def _is_partner_role(role: str) -> bool:
    return role.startswith("partner_")


def _permissions_for(role: str) -> list[str]:
    if _is_platform_role(role):
        permissions = [
            "PLATFORM_TENANT_VIEW",
            "PLATFORM_PLAN_CRUD",
            "PLATFORM_AUDIT_VIEW",
            "PLATFORM_USER_MANAGE",
        ]
        if role == "platform_superroot":
            permissions.append("PLATFORM_AI_PROVIDER_MANAGE")
        return permissions
    if _is_partner_role(role):
        permissions = [
            "PARTNER_TENANT_VIEW",
            "PARTNER_INVOICE_READ",
            "PARTNER_DASHBOARD_VIEW",
            "PARTNER_CLIENT_VIEW",
        ]
        if role in {"partner_reseller", "partner_operator"}:
            permissions.extend(
                [
                    "PARTNER_INVOICE_EMIT",
                    "PARTNER_CLIENT_MANAGE",
                ]
            )
        if role == "partner_reseller":
            permissions.append("PARTNER_USER_MANAGE")
        return permissions
    return [
        "TENANT_INVOICE_READ",
        "TENANT_INVOICE_EMIT",
        "TENANT_RFCE_SUBMIT",
        "TENANT_APPROVAL_SEND",
        "TENANT_CERT_UPLOAD",
        "TENANT_CHAT_ASSIST",
        "TENANT_PLAN_VIEW",
        "TENANT_PLAN_UPGRADE",
        "TENANT_USAGE_VIEW",
    ]


def _issue_tokens(*, user_id: str, tenant_id: int, role: str) -> tuple[str, str]:
    access_payload: dict[str, Any] = {"sub": user_id, "tenant_id": tenant_id, "role": role}
    refresh_payload: dict[str, Any] = {"sub": user_id, "tenant_id": tenant_id, "scope": "refresh"}
    refresh_exp = dt.timedelta(minutes=settings.refresh_token_exp_minutes)
    return create_jwt(access_payload), create_jwt(refresh_payload, refresh_exp)


def _normalize_login_identifier(identifier: str) -> str:
    ident = (identifier or "").strip()
    if not ident:
        return ident

    # Allow short usernames for the bootstrap admin (e.g. "admin" -> "admin@getupsoft.com.do")
    bootstrap_email = (settings.bootstrap_admin_email or "").strip()
    if bootstrap_email:
        localpart = bootstrap_email.split("@", 1)[0]
        if "@" not in ident and ident.lower() == localpart.lower():
            return bootstrap_email
    return ident


@router.post("/login", response_model=_LoginResponse)
async def login(payload: _LoginPayload, service: AuthService = Depends(get_service)) -> _LoginResponse:
    email = _normalize_login_identifier(payload.email)

    if settings.bootstrap_admin_enabled and email.lower() == settings.bootstrap_admin_email.lower():
        service.bootstrap_admin(None)

    user, tokens = service.authenticate(email, payload.password)
    mfa_required = settings.mfa_enabled and bool(user.mfa_secret)
    scope_value: Literal["PLATFORM", "TENANT", "PARTNER"]
    if _is_platform_role(user.role):
        scope_value = "PLATFORM"
    elif _is_partner_role(user.role):
        scope_value = "PARTNER"
    else:
        scope_value = "TENANT"
    permissions = _permissions_for(user.role)
    tenant_id_out = str(user.tenant_id) if scope_value == "TENANT" else None

    if mfa_required:
        return _LoginResponse(
            access_token="",
            refresh_token="",
            user=_UserPayload(
                id=str(user.id),
                email=user.email,
                scope=scope_value,
                tenant_id=tenant_id_out,
                roles=[user.role],
            ),
            permissions=permissions,
            mfa_required=True,
        )

    return _LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user=_UserPayload(
            id=str(user.id),
            email=user.email,
            scope=scope_value,
            tenant_id=tenant_id_out,
            roles=[user.role],
        ),
        permissions=permissions,
        mfa_required=False,
    )


@router.post("/mfa/verify", response_model=_AuthSession)
async def verify_mfa(payload: _MFAPayload, service: AuthService = Depends(get_service)) -> _AuthSession:
    if not settings.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA deshabilitado")
    if not service.verify_mfa(payload.email, payload.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA inválido")

    user = service.repository.get_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    access_token, refresh_token = _issue_tokens(user_id=str(user.id), tenant_id=user.tenant_id, role=user.role)
    scope_value: Literal["PLATFORM", "TENANT", "PARTNER"]
    if _is_platform_role(user.role):
        scope_value = "PLATFORM"
    elif _is_partner_role(user.role):
        scope_value = "PARTNER"
    else:
        scope_value = "TENANT"
    permissions = _permissions_for(user.role)
    tenant_id_out = str(user.tenant_id) if scope_value == "TENANT" else None

    return _AuthSession(
        accessToken=access_token,
        refreshToken=refresh_token,
        user=_AuthUser(
            id=str(user.id),
            email=user.email,
            scope=scope_value,
            tenantId=tenant_id_out,
            roles=[user.role],
        ),
        permissions=permissions,
    )


@me_router.get("/me", response_model=_LoginResponse)
async def me(
    authorization: str = Header(..., alias="Authorization"),
    service: AuthService = Depends(get_service),
) -> _LoginResponse:
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

    user_obj = service.repository.db.get(User, user_pk)
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    scope_value: Literal["PLATFORM", "TENANT", "PARTNER"]
    if _is_platform_role(user_obj.role):
        scope_value = "PLATFORM"
    elif _is_partner_role(user_obj.role):
        scope_value = "PARTNER"
    else:
        scope_value = "TENANT"
    permissions = _permissions_for(user_obj.role)
    tenant_id_out = str(user_obj.tenant_id) if scope_value == "TENANT" else None

    access_token, refresh_token = _issue_tokens(
        user_id=str(user_obj.id),
        tenant_id=user_obj.tenant_id,
        role=user_obj.role,
    )
    return _LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_UserPayload(
            id=str(user_obj.id),
            email=user_obj.email,
            scope=scope_value,
            tenant_id=tenant_id_out,
            roles=[user_obj.role],
        ),
        permissions=permissions,
        mfa_required=False,
    )
