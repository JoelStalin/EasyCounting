"""Shared portal authentication helpers for password/social login flows."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import secrets
from typing import Any, Literal

import pyotp
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_control import (
    RecoveryCode,
    RoleChangeRequest,
    SensitiveActionToken,
    TenantMembership,
    UserSession,
    WebAuthnCredential,
)
from app.infra.settings import settings
from app.models.accounting import TenantSettings
from app.models.authn import AuthLoginChallenge, AuthLoginTicket, UserExternalIdentity
from app.models.billing import Plan
from app.models.profile import FiscalProfile, UserProfile
from app.models.tenant import Tenant
from app.models.user import User
from app.models.ui_tour import UserViewTour
from app.security.audit import append_audit_log
from app.security.enums import GlobalRole, Permission, TenantRole
from app.security.permissions import (
    derive_global_role,
    derive_tenant_role,
    permission_names,
    permissions_for_assignment,
    scope_name,
)
from app.services.email_service import EmailConfigurationError, EmailDeliveryError, EmailPayload, get_email_service
from app.shared.security import create_jwt, hash_password, verify_password
from app.shared.time import utcnow

PortalKind = Literal["admin", "client", "seller"]
AuthScope = Literal["PLATFORM", "TENANT", "PARTNER"]


def is_platform_role(role: str) -> bool:
    return role.startswith("platform_")


def is_partner_role(role: str) -> bool:
    return role.startswith("partner_")


def scope_for_role(role: str) -> AuthScope:
    return scope_name(
        global_role=derive_global_role(None, role),
        tenant_role=derive_tenant_role(None, role),
        legacy_role=role,
    )  # type: ignore[return-value]


def permissions_for_role(role: str) -> list[str]:
    return permission_names(
        permissions_for_assignment(
            global_role=derive_global_role(None, role),
            tenant_role=derive_tenant_role(None, role),
            legacy_role=role,
        )
    )


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

    def _legacy_global_role(self, user: User) -> GlobalRole:
        return derive_global_role(user.global_role, user.role)

    def _legacy_tenant_role(self, user: User) -> TenantRole | None:
        return derive_tenant_role(None, user.role)

    def _ensure_user_profile(self, user: User, *, display_name: str | None = None) -> UserProfile:
        if user.profile:
            return user.profile
        first_name = None
        last_name = None
        if display_name:
            chunks = [part for part in display_name.strip().split(" ") if part]
            if chunks:
                first_name = chunks[0]
                last_name = " ".join(chunks[1:]) or None
        profile = UserProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            alternate_email=user.email,
            phone_primary=user.phone,
        )
        self.db.add(profile)
        self.db.flush()
        return profile

    def _ensure_tenant_membership(self, user: User) -> TenantMembership | None:
        active = self.db.scalar(
            select(TenantMembership).where(
                TenantMembership.user_id == user.id,
                TenantMembership.tenant_id == user.tenant_id,
                TenantMembership.status == "active",
            )
        )
        if active:
            return active
        role = self._legacy_tenant_role(user)
        if role is None:
            return None
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=user.tenant_id,
            role=role.value,
            status="active",
            is_default=True,
        )
        self.db.add(membership)
        self.db.flush()
        return membership

    def _ensure_fiscal_profile(self, *, user: User | None = None, tenant: Tenant | None = None, email: str | None = None) -> FiscalProfile:
        if user is None and tenant is None:
            raise ValueError("user o tenant requerido para crear fiscal profile")
        existing = user.fiscal_profile if user is not None else tenant.fiscal_profile
        if existing:
            return existing
        profile = FiscalProfile(
            owner_type="USER" if user is not None else "TENANT",
            user_id=user.id if user is not None else None,
            tenant_id=tenant.id if tenant is not None else None,
            email=email or (user.email if user is not None else None),
            phone=user.phone if user is not None else None,
            country="DO",
        )
        self.db.add(profile)
        self.db.flush()
        return profile

    def _effective_permissions(self, user: User) -> list[str]:
        membership = self._resolve_membership(user)
        return permission_names(
            permissions_for_assignment(
                global_role=self._legacy_global_role(user),
                tenant_role=derive_tenant_role(membership.role if membership else None, user.role),
                legacy_role=user.role,
            )
        )

    def bootstrap_admin_if_needed(self, email: str) -> User | None:
        normalized_email = normalize_login_identifier(email)
        if not settings.bootstrap_admin_enabled or normalized_email.lower() != settings.bootstrap_admin_email.lower():
            return None
        existing = self.get_user_by_email(normalized_email)
        if existing:
            self._ensure_tenant_membership(existing)
            return existing
        tenant = self.db.query(Tenant).order_by(Tenant.id.asc()).first()
        if not tenant:
            tenant = Tenant(
                name="Platform",
                rnc="00000000000",
                tenant_kind="MATRIX",
                certification_status="certified",
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
            global_role=derive_global_role(None, settings.bootstrap_admin_role).value,
            status="activo",
        )
        self.db.add(admin)
        self.db.flush()
        self._ensure_user_profile(admin)
        self._ensure_fiscal_profile(tenant=tenant, email=settings.bootstrap_admin_email)
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
        self._ensure_tenant_membership(user)
        return user

    def _resolve_membership(self, user: User) -> TenantMembership | None:
        return self._ensure_tenant_membership(user)

    def issue_tokens(
        self,
        *,
        user_id: str,
        tenant_id: int,
        role: str,
        membership_id: int | None = None,
        global_role: str | None = None,
        session_key: str | None = None,
        scopes: list[str] | None = None,
    ) -> tuple[str, str]:
        access_payload: dict[str, Any] = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "active_tenant_id": tenant_id,
            "role": role,
            "membership_id": membership_id,
            "global_role": global_role or derive_global_role(None, role).value,
            "sid": session_key,
            "scope": ",".join(scopes or []),
        }
        refresh_payload: dict[str, Any] = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "active_tenant_id": tenant_id,
            "membership_id": membership_id,
            "sid": session_key,
            "scope": "refresh",
        }
        refresh_exp = dt.timedelta(minutes=settings.refresh_token_exp_minutes)
        return create_jwt(access_payload), create_jwt(refresh_payload, refresh_exp)

    def serialize_user(self, user: User) -> dict[str, Any]:
        membership = self._resolve_membership(user)
        scope = scope_name(
            global_role=self._legacy_global_role(user),
            tenant_role=derive_tenant_role(membership.role if membership else None, user.role),
            legacy_role=user.role,
        )
        return {
            "id": str(user.id),
            "email": user.email,
            "scope": scope,
            "tenant_id": str(user.tenant_id) if scope in {"TENANT", "PARTNER"} else None,
            "roles": [user.global_role, membership.role if membership else user.role],
            "onboarding_status": user.tenant.onboarding_status if user.tenant else None,
            "membership_id": membership.id if membership else None,
            "global_role": user.global_role,
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
            "permissions": self._effective_permissions(user),
            "mfa_required": mfa_required,
            "challenge_id": challenge_id,
        }

    def _create_session_record(
        self,
        user: User,
        *,
        membership: TenantMembership | None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[UserSession, str]:
        session_key = secrets.token_urlsafe(24)
        refresh_seed = secrets.token_urlsafe(32)
        record = UserSession(
            user_id=user.id,
            membership_id=membership.id if membership else None,
            active_tenant_id=user.tenant_id,
            session_key=session_key,
            refresh_token_hash=self._digest(refresh_seed),
            scope=scope_for_role(user.role),
            user_agent=user_agent,
            ip_address=ip_address,
            last_seen_at=utcnow(),
            expires_at=utcnow() + dt.timedelta(minutes=settings.refresh_token_exp_minutes),
        )
        self.db.add(record)
        self.db.flush()
        return record, refresh_seed

    def build_auth_session(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        membership = self._resolve_membership(user)
        session_record, _refresh_seed = self._create_session_record(
            user,
            membership=membership,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        access_token, refresh_token = self.issue_tokens(
            user_id=str(user.id),
            tenant_id=user.tenant_id,
            role=user.role,
            membership_id=membership.id if membership else None,
            global_role=user.global_role,
            session_key=session_record.session_key,
        )
        serialized = self.serialize_user(user)
        user.last_login_at = utcnow()
        self.db.flush()
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
            "permissions": self._effective_permissions(user),
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

    def verify_login_challenge(
        self,
        *,
        challenge_id: str,
        code: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
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
        return self.build_auth_session(user, user_agent=user_agent, ip_address=ip_address)

    def list_sessions(self, user: User) -> list[UserSession]:
        return self.db.scalars(
            select(UserSession).where(UserSession.user_id == user.id).order_by(UserSession.created_at.desc())
        ).all()

    def revoke_session(self, *, user: User, session_id: int) -> UserSession:
        record = self.db.get(UserSession, session_id)
        if not record or record.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesion no encontrada")
        record.revoked_at = utcnow()
        self.db.flush()
        return record

    def revoke_all_sessions_for_user(self, user: User) -> None:
        for record in self.list_sessions(user):
            if record.revoked_at is None:
                record.revoked_at = utcnow()
        self.db.flush()

    def create_sensitive_action_token(
        self,
        *,
        user: User,
        purpose: str,
        target_value: str | None = None,
        metadata: dict[str, Any] | None = None,
        ttl_minutes: int = 15,
    ) -> str:
        for record in self.db.scalars(
            select(SensitiveActionToken).where(
                SensitiveActionToken.user_id == user.id,
                SensitiveActionToken.purpose == purpose,
                SensitiveActionToken.used_at.is_(None),
            )
        ).all():
            record.used_at = utcnow()
        raw = secrets.token_urlsafe(32)
        token = SensitiveActionToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=self._digest(raw),
            target_value=target_value,
            metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
            expires_at=utcnow() + dt.timedelta(minutes=ttl_minutes),
        )
        self.db.add(token)
        self.db.flush()
        return raw

    def consume_sensitive_action_token(self, *, user: User, purpose: str, token: str) -> SensitiveActionToken:
        record = self.db.scalar(
            select(SensitiveActionToken).where(
                SensitiveActionToken.user_id == user.id,
                SensitiveActionToken.purpose == purpose,
                SensitiveActionToken.token_hash == self._digest(token),
            )
        )
        if not record or record.used_at is not None or record.expires_at < utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sensible invalido o expirado")
        record.used_at = utcnow()
        self.db.flush()
        return record

    def request_password_reset(self, email: str) -> None:
        user = self.get_user_by_email(normalize_login_identifier(email))
        if not user:
            return
        raw_token = self.create_sensitive_action_token(user=user, purpose="password_reset", ttl_minutes=15)
        self._send_security_email(
            to=user.email,
            subject="Restablecimiento de contraseña GetUpSoft",
            text_body=(
                "Se solicitó restablecer su contraseña.\n"
                f"Token de confirmación: {raw_token}\n"
                "Este token expira en 15 minutos y solo puede usarse una vez."
            ),
        )

    def reset_password_with_token(self, *, token: str, new_password: str) -> None:
        record = self.db.scalar(
            select(SensitiveActionToken).where(
                SensitiveActionToken.purpose == "password_reset",
                SensitiveActionToken.token_hash == self._digest(token),
            )
        )
        if not record or record.used_at is not None or record.expires_at < utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de restablecimiento invalido")
        user = self.get_user_by_id(record.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        user.password_hash = hash_password(new_password)
        user.last_password_changed_at = utcnow()
        record.used_at = utcnow()
        self.revoke_all_sessions_for_user(user)
        self.db.flush()

    def initiate_password_change(self, *, user: User, current_password: str, new_password: str) -> str:
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña actual invalida")
        raw_token = self.create_sensitive_action_token(
            user=user,
            purpose="password_change",
            metadata={"new_password_hash": hash_password(new_password)},
            ttl_minutes=15,
        )
        self._send_security_email(
            to=user.email,
            subject="Confirmación de cambio de contraseña",
            text_body=(
                "Use este token para confirmar el cambio de contraseña.\n"
                f"Token: {raw_token}\n"
                "Debe completar también MFA antes de aplicar el cambio."
            ),
        )
        return raw_token

    def confirm_password_change(self, *, user: User, token: str, mfa_code: str | None) -> None:
        if user.mfa_secret:
            if not mfa_code:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Codigo MFA requerido")
            if not pyotp.TOTP(user.mfa_secret).verify(mfa_code, valid_window=1):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Codigo MFA invalido")
        record = self.consume_sensitive_action_token(user=user, purpose="password_change", token=token)
        metadata = json.loads(record.metadata_json or "{}")
        new_password_hash = metadata.get("new_password_hash")
        if not new_password_hash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token de cambio sin payload util")
        user.password_hash = str(new_password_hash)
        user.last_password_changed_at = utcnow()
        self.revoke_all_sessions_for_user(user)
        self.db.flush()

    def _send_security_email(self, *, to: str, subject: str, text_body: str) -> None:
        try:
            get_email_service().send(
                EmailPayload(
                    to=to,
                    subject=subject,
                    text_body=text_body,
                )
            )
        except (EmailConfigurationError, EmailDeliveryError):
            # Keep flows operable in local/test environments without SMTP, while the token
            # persists safely in the database for controlled validation.
            return

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
            tenant_kind="STANDARD",
            certification_status="pending",
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
            global_role=GlobalRole.USER.value,
            status="activo",
        )
        self.db.add(user)
        self.db.flush()
        self._ensure_user_profile(user, display_name=display_name)
        self._ensure_fiscal_profile(user=user, email=email)
        self._ensure_fiscal_profile(tenant=tenant, email=email)
        self._ensure_tenant_membership(user)
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
