"""Shared portal authentication helpers for password/social login flows."""
from __future__ import annotations

import datetime as dt
import hashlib
import secrets
from typing import Any, Literal

import pyotp
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.settings import settings
from app.models.accounting import TenantSettings
from app.models.authn import AuthLoginChallenge, AuthLoginTicket, UserExternalIdentity
from app.models.billing import Plan
from app.models.tenant import Tenant
from app.models.user import User
from app.models.ui_tour import UserViewTour
from app.shared.security import create_jwt, hash_password, verify_password
from app.shared.time import utcnow

PortalKind = Literal["admin", "client", "seller"]
AuthScope = Literal["PLATFORM", "TENANT", "PARTNER"]


def is_platform_role(role: str) -> bool:
    return role.startswith("platform_")


def is_partner_role(role: str) -> bool:
    return role.startswith("partner_")


def scope_for_role(role: str) -> AuthScope:
    if is_platform_role(role):
        return "PLATFORM"
    if is_partner_role(role):
        return "PARTNER"
    return "TENANT"


def permissions_for_role(role: str) -> list[str]:
    if is_platform_role(role):
        permissions = [
            "PLATFORM_TENANT_VIEW",
            "PLATFORM_PLAN_CRUD",
            "PLATFORM_AUDIT_VIEW",
            "PLATFORM_USER_MANAGE",
        ]
        if role == "platform_superroot":
            permissions.append("PLATFORM_AI_PROVIDER_MANAGE")
        return permissions
    if is_partner_role(role):
        permissions = [
            "PARTNER_TENANT_VIEW",
            "PARTNER_INVOICE_READ",
            "PARTNER_DASHBOARD_VIEW",
            "PARTNER_CLIENT_VIEW",
        ]
        if role in {"partner_reseller", "partner_operator"}:
            permissions.extend(["PARTNER_INVOICE_EMIT", "PARTNER_CLIENT_MANAGE"])
        if role == "partner_reseller":
            permissions.append("PARTNER_USER_MANAGE")
        return permissions
    return [
        "TENANT_INVOICE_READ",
        "TENANT_INVOICE_EMIT",
        "TENANT_RECURRING_INVOICE_MANAGE",
        "TENANT_RFCE_SUBMIT",
        "TENANT_APPROVAL_SEND",
        "TENANT_CERT_UPLOAD",
        "TENANT_CHAT_ASSIST",
        "TENANT_API_TOKEN_MANAGE",
        "TENANT_PLAN_VIEW",
        "TENANT_PLAN_UPGRADE",
        "TENANT_USAGE_VIEW",
    ]


def normalize_login_identifier(identifier: str) -> str:
    ident = (identifier or "").strip()
    if not ident:
        return ident
    bootstrap_email = (settings.bootstrap_admin_email or "").strip()
    if bootstrap_email:
        localpart = bootstrap_email.split("@", 1)[0]
        if "@" not in ident and ident.lower() == localpart.lower():
            return bootstrap_email
    return ident


class PortalAuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def bootstrap_admin_if_needed(self, email: str) -> User | None:
        normalized_email = normalize_login_identifier(email)
        if not settings.bootstrap_admin_enabled or normalized_email.lower() != settings.bootstrap_admin_email.lower():
            return None
        existing = self.get_user_by_email(normalized_email)
        if existing:
            return existing
        tenant = self.db.query(Tenant).order_by(Tenant.id.asc()).first()
        if not tenant:
            tenant = Tenant(
                name="Platform",
                rnc="00000000000",
                env="PRECERT",
                onboarding_status="completed",
                dgii_base_ecf="",
                dgii_base_fc="",
            )
            self.db.add(tenant)
            self.db.flush()
        mfa_secret = pyotp.random_base32() if settings.mfa_enabled else ""
        admin = User(
            tenant_id=tenant.id,
            email=settings.bootstrap_admin_email,
            phone=settings.bootstrap_admin_phone,
            password_hash=hash_password(settings.bootstrap_admin_password),
            mfa_secret=mfa_secret,
            role=settings.bootstrap_admin_role,
            status="activo",
        )
        self.db.add(admin)
        self.db.flush()
        return admin

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def authenticate_password(self, email: str, password: str) -> User:
        normalized = normalize_login_identifier(email)
        self.bootstrap_admin_if_needed(normalized)
        user = self.get_user_by_email(normalized)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")
        return user

    def issue_tokens(self, *, user_id: str, tenant_id: int, role: str) -> tuple[str, str]:
        access_payload: dict[str, Any] = {"sub": user_id, "tenant_id": tenant_id, "role": role}
        refresh_payload: dict[str, Any] = {"sub": user_id, "tenant_id": tenant_id, "scope": "refresh"}
        refresh_exp = dt.timedelta(minutes=settings.refresh_token_exp_minutes)
        return create_jwt(access_payload), create_jwt(refresh_payload, refresh_exp)

    def serialize_user(self, user: User) -> dict[str, Any]:
        scope = scope_for_role(user.role)
        return {
            "id": str(user.id),
            "email": user.email,
            "scope": scope,
            "tenant_id": str(user.tenant_id) if scope == "TENANT" else None,
            "roles": [user.role],
            "onboarding_status": user.tenant.onboarding_status if scope == "TENANT" and user.tenant else None,
        }

    def build_login_response(
        self,
        user: User,
        *,
        access_token: str = "",
        refresh_token: str = "",
        mfa_required: bool = False,
        challenge_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": self.serialize_user(user),
            "permissions": permissions_for_role(user.role),
            "mfa_required": mfa_required,
            "challenge_id": challenge_id,
        }

    def build_auth_session(self, user: User) -> dict[str, Any]:
        access_token, refresh_token = self.issue_tokens(
            user_id=str(user.id),
            tenant_id=user.tenant_id,
            role=user.role,
        )
        serialized = self.serialize_user(user)
        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "user": {
                "id": serialized["id"],
                "email": serialized["email"],
                "scope": serialized["scope"],
                "tenantId": serialized["tenant_id"],
                "roles": serialized["roles"],
                "onboardingStatus": serialized["onboarding_status"],
            },
            "permissions": permissions_for_role(user.role),
        }

    def create_login_challenge(self, user: User, *, portal: PortalKind, provider: str) -> str:
        raw = secrets.token_urlsafe(32)
        now = utcnow()
        challenge = AuthLoginChallenge(
            user_id=user.id,
            portal=portal,
            provider=provider,
            challenge_hash=self._digest(raw),
            expires_at=now + dt.timedelta(minutes=10),
        )
        self.db.add(challenge)
        self.db.flush()
        return raw

    def verify_login_challenge(self, *, challenge_id: str, code: str) -> dict[str, Any]:
        challenge = self.db.scalar(
            select(AuthLoginChallenge).where(AuthLoginChallenge.challenge_hash == self._digest(challenge_id))
        )
        if not challenge or challenge.consumed_at or challenge.expires_at < utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Challenge MFA invalido o expirado")
        user = self.get_user_by_id(challenge.user_id)
        if not user or not user.mfa_secret:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario MFA no encontrado")
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Codigo MFA invalido")
        challenge.consumed_at = utcnow()
        self.db.flush()
        return self.build_auth_session(user)

    def create_login_ticket(self, user: User, *, portal: PortalKind, return_to: str | None) -> str:
        raw = secrets.token_urlsafe(32)
        ticket = AuthLoginTicket(
            user_id=user.id,
            portal=portal,
            ticket_hash=self._digest(raw),
            return_to=return_to,
            expires_at=utcnow() + dt.timedelta(minutes=5),
        )
        self.db.add(ticket)
        self.db.flush()
        return raw

    def consume_login_ticket(self, ticket: str, *, portal: PortalKind) -> tuple[User, str | None]:
        record = self.db.scalar(select(AuthLoginTicket).where(AuthLoginTicket.ticket_hash == self._digest(ticket)))
        if not record or record.portal != portal or record.consumed_at or record.expires_at < utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ticket de login invalido o expirado")
        user = self.get_user_by_id(record.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        record.consumed_at = utcnow()
        self.db.flush()
        return user, record.return_to

    def get_external_identity(self, *, provider: str, provider_subject: str) -> UserExternalIdentity | None:
        return self.db.scalar(
            select(UserExternalIdentity).where(
                UserExternalIdentity.provider == provider,
                UserExternalIdentity.provider_subject == provider_subject,
            )
        )

    def link_external_identity(
        self,
        *,
        user: User,
        provider: str,
        provider_subject: str,
        email: str,
        email_verified: bool,
        display_name: str | None,
        avatar_url: str | None,
    ) -> UserExternalIdentity:
        identity = self.get_external_identity(provider=provider, provider_subject=provider_subject)
        now = utcnow()
        if identity:
            identity.user_id = user.id
            identity.email = email
            identity.email_verified = email_verified
            identity.display_name = display_name
            identity.avatar_url = avatar_url
            identity.last_login_at = now
            self.db.flush()
            return identity
        identity = UserExternalIdentity(
            user_id=user.id,
            provider=provider,
            provider_subject=provider_subject,
            email=email,
            email_verified=email_verified,
            display_name=display_name,
            avatar_url=avatar_url,
            last_login_at=now,
        )
        self.db.add(identity)
        self.db.flush()
        return identity

    def ensure_portal_access(self, *, user: User, portal: PortalKind) -> None:
        scope = scope_for_role(user.role)
        if portal == "admin" and scope != "PLATFORM":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta no autorizada para Admin")
        if portal == "seller" and scope != "PARTNER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta no autorizada para Socios")
        if portal == "client" and scope != "TENANT":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta no autorizada para Clientes")

    def resolve_social_user(
        self,
        *,
        portal: PortalKind,
        provider: str,
        provider_subject: str,
        email: str | None,
        email_verified: bool,
        display_name: str | None,
        avatar_url: str | None,
    ) -> tuple[User, bool]:
        identity = self.get_external_identity(provider=provider, provider_subject=provider_subject)
        if identity:
            user = self.get_user_by_id(identity.user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario enlazado no encontrado")
            self.ensure_portal_access(user=user, portal=portal)
            self.link_external_identity(
                user=user,
                provider=provider,
                provider_subject=provider_subject,
                email=email or identity.email,
                email_verified=email_verified or identity.email_verified,
                display_name=display_name or identity.display_name,
                avatar_url=avatar_url or identity.avatar_url,
            )
            return user, False

        if email:
            user = self.get_user_by_email(email)
            if user:
                self.ensure_portal_access(user=user, portal=portal)
                self.link_external_identity(
                    user=user,
                    provider=provider,
                    provider_subject=provider_subject,
                    email=email,
                    email_verified=email_verified,
                    display_name=display_name,
                    avatar_url=avatar_url,
                )
                return user, False

        if portal != "client":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La cuenta social no esta preautorizada para este portal",
            )
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El proveedor no devolvio un email utilizable")

        user = self._create_preliminary_tenant_user(email=email, display_name=display_name)
        self.link_external_identity(
            user=user,
            provider=provider,
            provider_subject=provider_subject,
            email=email,
            email_verified=email_verified,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        return user, True

    def list_tours(self, user_id: int) -> list[UserViewTour]:
        return self.db.scalars(
            select(UserViewTour).where(UserViewTour.user_id == user_id).order_by(UserViewTour.view_key.asc())
        ).all()

    def upsert_tour(
        self,
        *,
        user_id: int,
        view_key: str,
        tour_version: int,
        status_value: str,
        last_step: int | None,
    ) -> UserViewTour:
        tour = self.db.scalar(
            select(UserViewTour).where(UserViewTour.user_id == user_id, UserViewTour.view_key == view_key)
        )
        if tour:
            tour.tour_version = tour_version
            tour.status = status_value
            tour.last_step = last_step
            tour.completed_at = utcnow() if status_value == "completed" else None
            self.db.flush()
            return tour
        tour = UserViewTour(
            user_id=user_id,
            view_key=view_key,
            tour_version=tour_version,
            status=status_value,
            last_step=last_step,
            completed_at=utcnow() if status_value == "completed" else None,
        )
        self.db.add(tour)
        self.db.flush()
        return tour

    def _create_preliminary_tenant_user(self, *, email: str, display_name: str | None) -> User:
        plan = self.db.scalar(select(Plan).where(Plan.name == "Emprendedor").limit(1))
        localpart = email.split("@", 1)[0]
        tenant = Tenant(
            name=(display_name or localpart).strip()[:255] or "Empresa nueva",
            rnc=self._next_temporary_rnc(),
            env="PRECERT",
            onboarding_status="pending_fiscal_setup",
            plan_id=plan.id if plan else None,
            dgii_base_ecf=str(settings.dgii_recepcion_base_url),
            dgii_base_fc=str(settings.dgii_recepcion_fc_base_url),
        )
        self.db.add(tenant)
        self.db.flush()
        self.db.add(
            TenantSettings(
                tenant_id=tenant.id,
                moneda="DOP",
                correo_facturacion=email,
                telefono_contacto="",
                notas="Cuenta preliminar creada por login social.",
            )
        )
        user = User(
            tenant_id=tenant.id,
            partner_account_id=None,
            email=email,
            phone="",
            password_hash=hash_password(secrets.token_urlsafe(24)),
            mfa_secret="",
            role="tenant_user",
            status="activo",
        )
        self.db.add(user)
        self.db.flush()
        return user

    def _next_temporary_rnc(self) -> str:
        prefix = "999"
        for _ in range(50):
            suffix = f"{secrets.randbelow(10**8):08d}"
            rnc = f"{prefix}{suffix}"
            exists = self.db.scalar(select(Tenant.id).where(Tenant.rnc == rnc))
            if not exists:
                return rnc
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo generar RNC temporal")

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
