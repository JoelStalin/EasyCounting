"""Authentication context dependencies and permission gates."""
from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_control import TenantMembership, UserSession
from app.models.user import User
from app.security.audit import append_audit_log
from app.security.enums import Permission
from app.security.permissions import derive_global_role, derive_tenant_role, permissions_for_assignment
from app.security.policies import AuthContext
from app.shared.database import get_db
from app.shared.security import decode_jwt


def _authorization_header(authorization: str | None = Header(default=None, alias="Authorization")) -> str | None:
    return authorization


def _coerce_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_auth_context(
    request: Request,
    authorization: Annotated[str | None, Depends(_authorization_header)],
    db: Session = Depends(get_db),
) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization invalido")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_jwt(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc

    subject = str(payload.get("sub", "")).strip()
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin sujeto valido")

    user = db.get(User, _coerce_int(subject)) if _coerce_int(subject) is not None else None
    session = None
    if isinstance(payload.get("sid"), str):
        session = db.scalar(select(UserSession).where(UserSession.session_key == payload["sid"]))
        if session and session.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesion revocada")

    membership = None
    membership_id = _coerce_int(payload.get("membership_id"))
    if user is not None and membership_id is not None:
        membership = db.scalar(
            select(TenantMembership).where(
                TenantMembership.id == membership_id,
                TenantMembership.user_id == user.id,
            )
        )

    active_tenant_id = _coerce_int(payload.get("active_tenant_id")) or _coerce_int(payload.get("tenant_id"))
    if user is not None and membership is None and active_tenant_id is not None:
        membership = db.scalar(
            select(TenantMembership).where(
                TenantMembership.user_id == user.id,
                TenantMembership.tenant_id == active_tenant_id,
                TenantMembership.status == "active",
            )
        )
    if active_tenant_id is None and membership is not None:
        active_tenant_id = membership.tenant_id
    if active_tenant_id is None and user is not None:
        active_tenant_id = user.tenant_id

    legacy_role = str(payload.get("role") or getattr(user, "role", "") or "").strip() or None
    global_role = derive_global_role(getattr(user, "global_role", None), legacy_role)
    tenant_role = derive_tenant_role(getattr(membership, "role", None), legacy_role)
    scopes = []
    raw_scope = payload.get("scope")
    if isinstance(raw_scope, str) and raw_scope:
        scopes = [part.strip() for part in raw_scope.split(",") if part.strip()]

    context = AuthContext(
        subject=subject,
        token_payload=payload,
        user=user,
        membership=membership,
        session=session,
        global_role=global_role,
        tenant_role=tenant_role,
        legacy_role=legacy_role,
        active_tenant_id=active_tenant_id,
        permission_set=permissions_for_assignment(
            global_role=global_role,
            tenant_role=tenant_role,
            legacy_role=legacy_role,
        ),
        scopes=scopes,
    )
    request.state.auth_context = context
    return context


def require_permissions(*permissions: Permission | str, require_persisted_user: bool = False):
    targets = [permission if isinstance(permission, Permission) else Permission(permission) for permission in permissions]

    def dependency(
        request: Request,
        context: AuthContext = Depends(get_auth_context),
        db: Session = Depends(get_db),
    ) -> AuthContext:
        if require_persisted_user and context.user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario autenticado no resuelto")
        missing = [permission for permission in targets if permission not in context.permission_set]
        if missing:
            tenant_id = context.active_tenant_id or getattr(context.user, "tenant_id", None)
            if tenant_id:
                append_audit_log(
                    db,
                    tenant_id=tenant_id,
                    actor=getattr(context.user, "email", context.subject),
                    actor_user_id=getattr(context.user, "id", None),
                    membership_id=getattr(context.membership, "id", None),
                    action="AUTHZ_DENY",
                    resource=str(request.url.path),
                    resource_type="http_route",
                    resource_id=request.method,
                    decision="DENY",
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    metadata={"missing_permissions": [item.value for item in missing]},
                )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        tenant_id = context.active_tenant_id or getattr(context.user, "tenant_id", None)
        if tenant_id:
            append_audit_log(
                db,
                tenant_id=tenant_id,
                actor=getattr(context.user, "email", context.subject),
                actor_user_id=getattr(context.user, "id", None),
                membership_id=getattr(context.membership, "id", None),
                action="AUTHZ_ALLOW",
                resource=str(request.url.path),
                resource_type="http_route",
                resource_id=request.method,
                decision="ALLOW",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                metadata={"permissions": [item.value for item in targets]},
            )
        return context

    return dependency
