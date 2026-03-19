"""Social authentication provider flows for Google, Facebook and Apple."""
from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import json
import secrets
from typing import Any, Literal
from urllib.parse import urlencode

from fastapi import HTTPException, Request, status
import httpx
from jose import jwt

from app.infra.settings import settings

SocialProvider = Literal["google", "facebook", "apple"]
PortalKind = Literal["admin", "client", "seller"]


@dataclass(slots=True)
class SocialProviderInfo:
    provider: SocialProvider
    label: str


@dataclass(slots=True)
class SocialProfile:
    provider: SocialProvider
    subject: str
    email: str | None
    email_verified: bool
    display_name: str | None
    avatar_url: str | None


@dataclass(slots=True)
class SocialCallbackResult:
    provider: SocialProvider
    portal: PortalKind
    profile: SocialProfile
    return_to: str | None


class SocialAuthService:
    def list_enabled_providers(self) -> list[SocialProviderInfo]:
        providers: list[SocialProviderInfo] = []
        if settings.social_google_enabled:
            providers.append(SocialProviderInfo(provider="google", label="Google"))
        if settings.social_facebook_enabled:
            providers.append(SocialProviderInfo(provider="facebook", label="Facebook"))
        if settings.social_apple_enabled:
            providers.append(SocialProviderInfo(provider="apple", label="Apple"))
        return providers

    def ensure_provider_enabled(self, provider: SocialProvider) -> None:
        enabled = {
            "google": settings.social_google_enabled,
            "facebook": settings.social_facebook_enabled,
            "apple": settings.social_apple_enabled,
        }[provider]
        if not settings.social_auth_enabled or not enabled:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor social no habilitado")

    def build_start_url(
        self,
        *,
        request: Request,
        provider: SocialProvider,
        portal: PortalKind,
        return_to: str | None,
    ) -> str:
        self.ensure_provider_enabled(provider)
        state = secrets.token_urlsafe(24)
        session_states = request.session.setdefault("social_auth_states", {})
        session_states[state] = {
            "provider": provider,
            "portal": portal,
            "return_to": return_to,
        }
        request.session["social_auth_states"] = session_states
        redirect_uri = self.callback_url(provider)

        if provider == "google":
            params = {
                "client_id": settings.social_google_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "prompt": "select_account",
            }
            return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

        if provider == "facebook":
            params = {
                "client_id": settings.social_facebook_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "email,public_profile",
                "state": state,
            }
            return "https://www.facebook.com/v20.0/dialog/oauth?" + urlencode(params)

        params = {
            "client_id": settings.social_apple_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "response_mode": "form_post",
            "scope": "name email",
            "state": state,
        }
        return "https://appleid.apple.com/auth/authorize?" + urlencode(params)

    async def resolve_callback(self, *, request: Request, provider: SocialProvider) -> SocialCallbackResult:
        self.ensure_provider_enabled(provider)
        data = await self._callback_payload(request)
        state = str(data.get("state") or "").strip()
        code = str(data.get("code") or "").strip()
        error = str(data.get("error") or "").strip()
        if error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Login social cancelado: {error}")
        if not state or not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Callback social incompleto")

        session_states = request.session.get("social_auth_states", {})
        state_data = session_states.pop(state, None)
        request.session["social_auth_states"] = session_states
        if not state_data or state_data.get("provider") != provider:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State de OAuth invalido")

        portal = state_data.get("portal")
        if portal not in {"admin", "client", "seller"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Portal social invalido")
        redirect_uri = self.callback_url(provider)

        if provider == "google":
            profile = await self._google_profile(code=code, redirect_uri=redirect_uri)
        elif provider == "facebook":
            profile = await self._facebook_profile(code=code, redirect_uri=redirect_uri)
        else:
            profile = await self._apple_profile(code=code, redirect_uri=redirect_uri, callback_payload=data)

        return SocialCallbackResult(
            provider=provider,
            portal=portal,
            profile=profile,
            return_to=state_data.get("return_to"),
        )

    def callback_url(self, provider: SocialProvider) -> str:
        return f"{settings.social_callback_base_url}/api/v1/auth/oauth/{provider}/callback"

    async def _google_profile(self, *, code: str, redirect_uri: str) -> SocialProfile:
        token_payload = await self._request_form(
            "https://oauth2.googleapis.com/token",
            {
                "code": code,
                "client_id": settings.social_google_client_id or "",
                "client_secret": settings.social_google_client_secret or "",
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        access_token = token_payload.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google no devolvio access_token")
        profile = await self._request_json(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        email_verified = bool(profile.get("email_verified"))
        if not email_verified:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Google requiere email verificado")
        return SocialProfile(
            provider="google",
            subject=str(profile.get("sub") or ""),
            email=profile.get("email"),
            email_verified=email_verified,
            display_name=profile.get("name"),
            avatar_url=profile.get("picture"),
        )

    async def _facebook_profile(self, *, code: str, redirect_uri: str) -> SocialProfile:
        params = {
            "client_id": settings.social_facebook_client_id or "",
            "client_secret": settings.social_facebook_client_secret or "",
            "redirect_uri": redirect_uri,
            "code": code,
        }
        token_payload = await self._request_json("https://graph.facebook.com/v20.0/oauth/access_token", params=params)
        access_token = token_payload.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facebook no devolvio access_token")
        profile = await self._request_json(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email,picture.width(256).height(256)", "access_token": access_token},
        )
        email = profile.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facebook no devolvio email; habilita el permiso email o enlaza la cuenta manualmente",
            )
        picture_data = profile.get("picture") or {}
        picture_url = None
        if isinstance(picture_data, dict):
            picture_inner = picture_data.get("data") or {}
            if isinstance(picture_inner, dict):
                picture_url = picture_inner.get("url")
        return SocialProfile(
            provider="facebook",
            subject=str(profile.get("id") or ""),
            email=email,
            email_verified=True,
            display_name=profile.get("name"),
            avatar_url=picture_url,
        )

    async def _apple_profile(
        self,
        *,
        code: str,
        redirect_uri: str,
        callback_payload: dict[str, Any],
    ) -> SocialProfile:
        token_payload = await self._request_form(
            "https://appleid.apple.com/auth/token",
            {
                "client_id": settings.social_apple_client_id or "",
                "client_secret": self._build_apple_client_secret(),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        id_token = token_payload.get("id_token")
        if not id_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Apple no devolvio id_token")
        claims = await self._verify_apple_id_token(id_token)

        callback_user = callback_payload.get("user")
        callback_user_json: dict[str, Any] = {}
        if isinstance(callback_user, str) and callback_user.strip():
            try:
                callback_user_json = json.loads(callback_user)
            except json.JSONDecodeError:
                callback_user_json = {}

        name_value = None
        name_block = callback_user_json.get("name")
        if isinstance(name_block, dict):
            parts = [str(name_block.get("firstName") or "").strip(), str(name_block.get("lastName") or "").strip()]
            name_value = " ".join(part for part in parts if part).strip() or None

        email = claims.get("email") or callback_user_json.get("email")
        email_verified = str(claims.get("email_verified", "false")).lower() == "true"

        return SocialProfile(
            provider="apple",
            subject=str(claims.get("sub") or ""),
            email=email,
            email_verified=email_verified,
            display_name=name_value,
            avatar_url=None,
        )

    async def _verify_apple_id_token(self, id_token: str) -> dict[str, Any]:
        jwks = await self._request_json("https://appleid.apple.com/auth/keys")
        keys = jwks.get("keys", [])
        if not isinstance(keys, list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Apple JWKS invalido")
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        matching_key = next((key for key in keys if key.get("kid") == kid), None)
        if not matching_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Apple key id no encontrada")
        return jwt.decode(
            id_token,
            matching_key,
            algorithms=[header.get("alg", "RS256")],
            audience=settings.social_apple_client_id,
            issuer="https://appleid.apple.com",
        )

    def _build_apple_client_secret(self) -> str:
        private_key = (settings.social_apple_private_key or "").strip()
        if not private_key and settings.social_apple_private_key_path:
            private_key = settings.social_apple_private_key_path.read_text(encoding="utf-8")
        now = int(dt.datetime.now(dt.timezone.utc).timestamp())
        payload = {
            "iss": settings.social_apple_team_id,
            "iat": now,
            "exp": now + 86400 * 30,
            "aud": "https://appleid.apple.com",
            "sub": settings.social_apple_client_id,
        }
        headers = {"kid": settings.social_apple_key_id}
        return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

    @staticmethod
    async def _callback_payload(request: Request) -> dict[str, Any]:
        if request.method.upper() == "POST":
            form = await request.form()
            return dict(form)
        return dict(request.query_params)

    @staticmethod
    async def _request_json(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OAuth upstream failed: {exc}") from exc
        payload = response.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Respuesta OAuth no valida")
        return payload

    @staticmethod
    async def _request_form(url: str, data: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OAuth upstream failed: {exc}") from exc
        payload = response.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Respuesta OAuth no valida")
        return payload
