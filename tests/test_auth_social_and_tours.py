from __future__ import annotations

from typing import Iterator

import pyotp
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.main import app
from app.models.base import Base
from app.models.partner import PartnerAccount
from app.models.tenant import Tenant
from app.models.user import User
from app.services.portal_auth import PortalAuthService
from app.shared.database import get_db
from app.shared.security import create_jwt, hash_password


def _client_with_sqlite() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
    Base.metadata.create_all(engine)

    def override_get_db() -> Iterator[Session]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), SessionLocal


def test_login_returns_mfa_challenge_and_verify_returns_session() -> None:
    client, SessionLocal = _client_with_sqlite()
    secret = pyotp.random_base32()
    with SessionLocal() as session:
        tenant = Tenant(
            name="Empresa MFA",
            rnc="11111111111",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add(tenant)
        session.flush()
        user = User(
            tenant_id=tenant.id,
            email="admin-mfa@getupsoft.com.do",
            phone="8095551000",
            password_hash=hash_password("Secret123!"),
            mfa_secret=secret,
            role="platform_admin",
            status="activo",
        )
        session.add(user)
        session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin-mfa@getupsoft.com.do", "password": "Secret123!", "portal": "admin"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mfa_required"] is True
    assert body["challenge_id"]

    verify = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": body["challenge_id"], "code": pyotp.TOTP(secret).now()},
    )
    app.dependency_overrides.clear()
    assert verify.status_code == 200
    session = verify.json()
    assert session["accessToken"]
    assert session["user"]["scope"] == "PLATFORM"


def test_social_provider_endpoints_list_and_start(monkeypatch) -> None:
    client, _SessionLocal = _client_with_sqlite()
    monkeypatch.setattr("app.services.social_auth.settings.social_auth_enabled", True)
    monkeypatch.setattr("app.services.social_auth.settings.social_google_enabled", True)
    monkeypatch.setattr("app.services.social_auth.settings.social_google_client_id", "google-client")
    monkeypatch.setattr("app.services.social_auth.settings.social_google_client_secret", "google-secret")

    providers = client.get("/api/v1/auth/oauth/providers", params={"portal": "client"})
    assert providers.status_code == 200
    assert providers.json() == [{"provider": "google", "label": "Google"}]

    start = client.get(
        "/api/v1/auth/oauth/google/start",
        params={"portal": "client", "return_to": "/dashboard"},
        follow_redirects=False,
    )
    app.dependency_overrides.clear()
    assert start.status_code == 302
    assert "accounts.google.com" in start.headers["location"]


def test_social_exchange_for_admin_requires_mfa() -> None:
    client, SessionLocal = _client_with_sqlite()
    secret = pyotp.random_base32()
    with SessionLocal() as session:
        tenant = Tenant(
            name="Empresa Social",
            rnc="22222222222",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add(tenant)
        session.flush()
        user = User(
            tenant_id=tenant.id,
            email="superroot@getupsoft.com.do",
            phone="8095552000",
            password_hash=hash_password("Secret123!"),
            mfa_secret=secret,
            role="platform_superroot",
            status="activo",
        )
        session.add(user)
        session.flush()
        ticket = PortalAuthService(session).create_login_ticket(user, portal="admin", return_to="/ai-providers")
        session.commit()

    response = client.post("/api/v1/auth/oauth/exchange", json={"ticket": ticket, "portal": "admin"})
    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["mfaRequired"] is True
    assert body["challengeId"]
    assert body["returnTo"] == "/ai-providers"


def test_ui_tours_can_be_saved_and_listed() -> None:
    client, SessionLocal = _client_with_sqlite()
    with SessionLocal() as session:
        tenant = Tenant(
            name="Empresa Tours",
            rnc="33333333333",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add(tenant)
        session.flush()
        user = User(
            tenant_id=tenant.id,
            email="cliente-tours@getupsoft.com.do",
            phone="8095553000",
            password_hash=hash_password("Tenant123!"),
            mfa_secret="",
            role="tenant_user",
            status="activo",
        )
        session.add(user)
        session.commit()
        token = create_jwt({"sub": str(user.id), "tenant_id": tenant.id, "role": "tenant_user"})

    headers = {"Authorization": f"Bearer {token}"}
    update = client.put(
        "/api/v1/ui-tours/client-dashboard",
        json={"tourVersion": 2, "status": "completed", "lastStep": 3},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["status"] == "completed"

    listed = client.get("/api/v1/ui-tours/me", headers=headers)
    app.dependency_overrides.clear()
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["viewKey"] == "client-dashboard"
    assert body[0]["tourVersion"] == 2
