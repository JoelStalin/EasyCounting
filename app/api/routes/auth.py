"""Portal authentication routes shared by admin, client and seller portals."""
from __future__ import annotations

from typing import Any, Literal
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.auth.portal_deps import get_authenticated_user
from app.infra.settings import settings
from app.models.user import User
from app.services.portal_auth import PortalAuthService, PortalKind
from app.services.social_auth import SocialAuthService, SocialProvider
from app.shared.database import get_db
from app.shared.security import decode_jwt

router = APIRouter()
me_router = APIRouter()


class AuthUserModel(BaseModel):
    id: str
    email: str
    scope: Literal["PLATFORM", "TENANT", "PARTNER"]
    tenant_id: str | None = Field(default=None, alias="tenant_id")
    roles: list[str]
    onboarding_status: str | None = Field(default=None, alias="onboarding_status")

    model_config = ConfigDict(populate_by_name=True)


class LoginRequest(BaseModel):
    email: str
    password: str
    portal: PortalKind | None = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: AuthUserModel
    permissions: list[str]
    mfa_required: bool
    challenge_id: str | None = None


class MFARequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=8)
    challenge_id: str | None = None
    email: str | None = None


class AuthSessionUser(BaseModel):
    id: str
    email: str
    scope: Literal["PLATFORM", "TENANT", "PARTNER"]
    tenantId: str | None = None
    roles: list[str]
    onboardingStatus: str | None = None


class AuthSessionResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: AuthSessionUser
    permissions: list[str]
    returnTo: str | None = None


class SocialProviderItem(BaseModel):
    provider: SocialProvider
    label: str


class SocialExchangeRequest(BaseModel):
    ticket: str
    portal: PortalKind


class SocialExchangePendingMFA(BaseModel):
    mfaRequired: Literal[True]
    challengeId: str
    permissions: list[str]
    user: AuthSessionUser
    returnTo: str | None = None


class TourErrorResponse(BaseModel):
    detail: str


def _portal_from_user(user: User) -> PortalKind:
    if user.role.startswith("platform_"):
        return "admin"
    if user.role.startswith("partner_"):
        return "seller"
    return "client"


def _portal_base_url(portal: PortalKind) -> str:
    raw = {
        "admin": settings.admin_portal_domain,
        "client": settings.client_portal_domain,
        "seller": settings.partner_portal_domain,
    }[portal].strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw.rstrip("/")
    return f"https://{raw}"


def _serialize_auth_session_user(raw: dict[str, Any]) -> AuthSessionUser:
    return AuthSessionUser(
        id=str(raw["id"]),
        email=str(raw["email"]),
        scope=raw["scope"],
        tenantId=raw.get("tenantId"),
        roles=list(raw["roles"]),
        onboardingStatus=raw.get("onboardingStatus"),
    )


def _current_access_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    service = PortalAuthService(db)
    user = service.authenticate_password(payload.email, payload.password)
    portal = payload.portal or _portal_from_user(user)
    service.ensure_portal_access(user=user, portal=portal)

    if user.mfa_secret:
        challenge_id = service.create_login_challenge(user, portal=portal, provider="password")
        response = service.build_login_response(
            user,
            mfa_required=True,
            challenge_id=challenge_id,
        )
        return LoginResponse.model_validate(response)

    access_token, refresh_token = service.issue_tokens(
        user_id=str(user.id),
        tenant_id=user.tenant_id,
        role=user.role,
    )
    response = service.build_login_response(
        user,
        access_token=access_token,
        refresh_token=refresh_token,
        mfa_required=False,
    )
    return LoginResponse.model_validate(response)


@router.post("/mfa/verify", response_model=AuthSessionResponse)
def verify_mfa(
    payload: MFARequest,
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    service = PortalAuthService(db)

    if payload.challenge_id:
        session = service.verify_login_challenge(challenge_id=payload.challenge_id, code=payload.code)
        return AuthSessionResponse.model_validate(session)

    # Backward-compatible path while the three portals migrate fully to challengeId.
    if not payload.email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="challenge_id o email requerido")

    user = service.get_user_by_email(payload.email.strip())
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario MFA no encontrado")
    challenge_id = service.create_login_challenge(user, portal=_portal_from_user(user), provider="password")
    session = service.verify_login_challenge(challenge_id=challenge_id, code=payload.code)
    return AuthSessionResponse.model_validate(session)


@me_router.get("/me", response_model=LoginResponse)
def me(
    request: Request,
    auth: tuple[User, dict[str, Any]] = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
) -> LoginResponse:
    user, payload = auth
    service = PortalAuthService(db)
    access_token = _current_access_token(request)
    refresh_token = ""
    if access_token is None:
        access_token, refresh_token = service.issue_tokens(
            user_id=str(user.id),
            tenant_id=user.tenant_id,
            role=user.role,
        )
    else:
        refresh_payload = {
            "sub": payload.get("sub", str(user.id)),
            "tenant_id": payload.get("tenant_id", user.tenant_id),
            "scope": "refresh",
        }
        from app.shared.security import create_jwt  # local import to avoid cycles in module import paths

        refresh_token = create_jwt(refresh_payload)

    return LoginResponse.model_validate(
        service.build_login_response(
            user,
            access_token=access_token,
            refresh_token=refresh_token,
            mfa_required=False,
        )
    )


@router.get("/oauth/providers", response_model=list[SocialProviderItem])
def list_social_providers(
    _portal: PortalKind | None = Query(default=None, alias="portal"),
) -> list[SocialProviderItem]:
    service = SocialAuthService()
    return [SocialProviderItem(provider=item.provider, label=item.label) for item in service.list_enabled_providers()]


@router.get("/oauth/{provider}/start")
def start_social_login(
    provider: SocialProvider,
    request: Request,
    portal: PortalKind = Query(...),
    return_to: str | None = Query(default=None),
) -> RedirectResponse:
    service = SocialAuthService()
    url = service.build_start_url(request=request, provider=provider, portal=portal, return_to=return_to)
    return RedirectResponse(url, status_code=status.HTTP_302_FOUND)


@router.get("/oauth/{provider}/callback")
@router.post("/oauth/{provider}/callback")
async def social_callback(
    provider: SocialProvider,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    social_service = SocialAuthService()
    auth_service = PortalAuthService(db)
    callback = await social_service.resolve_callback(request=request, provider=provider)
    user, _created = auth_service.resolve_social_user(
        portal=callback.portal,
        provider=callback.provider,
        provider_subject=callback.profile.subject,
        email=callback.profile.email,
        email_verified=callback.profile.email_verified,
        display_name=callback.profile.display_name,
        avatar_url=callback.profile.avatar_url,
    )
    auth_service.ensure_portal_access(user=user, portal=callback.portal)
    ticket = auth_service.create_login_ticket(user, portal=callback.portal, return_to=callback.return_to)
    params = urlencode({"ticket": ticket})
    target = f"{_portal_base_url(callback.portal)}/auth/callback?{params}"
    return RedirectResponse(target, status_code=status.HTTP_302_FOUND)


@router.post(
    "/oauth/exchange",
    responses={401: {"model": TourErrorResponse}, 403: {"model": TourErrorResponse}},
)
def social_exchange(
    payload: SocialExchangeRequest,
    db: Session = Depends(get_db),
) -> AuthSessionResponse | SocialExchangePendingMFA:
    service = PortalAuthService(db)
    user, return_to = service.consume_login_ticket(payload.ticket, portal=payload.portal)
    service.ensure_portal_access(user=user, portal=payload.portal)

    if user.mfa_secret:
        challenge_id = service.create_login_challenge(user, portal=payload.portal, provider="social")
        session = service.build_auth_session(user)
        return SocialExchangePendingMFA(
            mfaRequired=True,
            challengeId=challenge_id,
            permissions=session["permissions"],
            user=_serialize_auth_session_user(session["user"]),
            returnTo=return_to,
        )

    session = service.build_auth_session(user)
    session["returnTo"] = return_to
    return AuthSessionResponse.model_validate(session)

