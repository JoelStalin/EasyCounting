from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.infra.settings import settings
from app.main import app
from app.models.base import Base
from app.models.invoice import Invoice
from app.models.platform_ai import PlatformAIProvider
from app.models.tenant import Tenant
from app.services.platform_ai import encrypt_secret
from app.shared.database import get_db
from app.shared.security import create_jwt


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


def _platform_headers(role: str) -> dict[str, str]:
    token = create_jwt({"sub": "1", "tenant_id": 1, "role": role})
    return {"Authorization": f"Bearer {token}"}


def _tenant_headers(tenant_id: int) -> dict[str, str]:
    token = create_jwt({"sub": f"user-{tenant_id}", "tenant_id": tenant_id, "role": "tenant_user"})
    return {"Authorization": f"Bearer {token}"}


def test_superroot_can_manage_platform_ai_providers() -> None:
    client, _SessionLocal = _client_with_sqlite()
    payload = {
        "displayName": "ChatGPT Plataforma",
        "providerType": "openai",
        "enabled": True,
        "isDefault": True,
        "model": "gpt-admin-test",
        "apiKey": "sk-test-secret-1234",
        "organizationId": "org_test",
        "projectId": "proj_test",
        "extraHeaders": {"X-Env": "admin"},
        "timeoutSeconds": 25,
        "maxCompletionTokens": 900,
    }

    create_response = client.post("/api/v1/admin/ai-providers", json=payload, headers=_platform_headers("platform_superroot"))
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["displayName"] == "ChatGPT Plataforma"
    assert created["providerType"] == "openai"
    assert created["apiKeyConfigured"] is True
    assert created["apiKeyMasked"].endswith("1234")
    assert created["apiKeyMasked"] != "sk-test-secret-1234"

    list_response = client.get("/api/v1/admin/ai-providers", headers=_platform_headers("platform_superroot"))
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["isDefault"] is True

    update_response = client.put(
        f"/api/v1/admin/ai-providers/{created['id']}",
        json={
            "displayName": "Gemini Plataforma",
            "providerType": "gemini",
            "enabled": True,
            "isDefault": False,
            "model": "gemini-admin-test",
            "clearApiKey": True,
            "timeoutSeconds": 18,
            "maxCompletionTokens": 700,
        },
        headers=_platform_headers("platform_superroot"),
    )
    app.dependency_overrides.clear()

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["displayName"] == "Gemini Plataforma"
    assert updated["providerType"] == "gemini"
    assert updated["apiKeyConfigured"] is False


def test_platform_admin_cannot_manage_platform_ai_providers() -> None:
    client, _SessionLocal = _client_with_sqlite()

    response = client.get("/api/v1/admin/ai-providers", headers=_platform_headers("platform_admin"))
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert "superroot" in response.json()["detail"]


def test_chatbot_uses_default_platform_ai_provider(monkeypatch) -> None:
    client, SessionLocal = _client_with_sqlite()
    monkeypatch.setattr(settings, "llm_chat_enabled", True)
    monkeypatch.setattr(settings, "llm_provider", "local")

    with SessionLocal() as session:
        tenant = Tenant(
            name="Empresa AI",
            rnc="12345678901",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add(tenant)
        session.flush()
        session.add(
            Invoice(
                tenant_id=tenant.id,
                encf="E310000000777",
                tipo_ecf="E31",
                xml_path="/tmp/openai.xml",
                xml_hash="hash-openai",
                estado_dgii="ACEPTADO",
                total=Decimal("325.00"),
                fecha_emision=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        session.add(
            PlatformAIProvider(
                display_name="ChatGPT Produccion",
                provider_type="openai",
                enabled=True,
                is_default=True,
                model="gpt-platform-live",
                encrypted_api_key=encrypt_secret("sk-platform-9999"),
                timeout_seconds=12,
                max_completion_tokens=450,
            )
        )
        session.commit()
        tenant_id = tenant.id

    captured: dict[str, object] = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Respuesta cloud controlada para el tenant autenticado.",
                        }
                    }
                ]
            }

    def fake_post(url: str, *, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setattr("app.application.tenant_chat.httpx.post", fake_post)

    response = client.post(
        "/api/v1/cliente/chat/ask",
        json={"question": "Analiza el riesgo operativo del comprobante E310000000777 y explica si requiere seguimiento."},
        headers=_tenant_headers(tenant_id),
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "openai"
    assert "Respuesta cloud controlada" in body["answer"]
    assert body["preprocess"]["dispatchStrategy"] == "provider_preferred"
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-platform-9999"


def test_chatbot_skips_external_provider_for_operational_question(monkeypatch) -> None:
    client, SessionLocal = _client_with_sqlite()
    monkeypatch.setattr(settings, "llm_chat_enabled", True)
    monkeypatch.setattr(settings, "llm_provider", "local")

    with SessionLocal() as session:
        tenant = Tenant(
            name="Empresa AI Local",
            rnc="12345678901",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add(tenant)
        session.flush()
        session.add(
            Invoice(
                tenant_id=tenant.id,
                encf="E310000000778",
                tipo_ecf="E31",
                xml_path="/tmp/local.xml",
                xml_hash="hash-local",
                estado_dgii="ACEPTADO",
                total=Decimal("520.00"),
                fecha_emision=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        session.add(
            PlatformAIProvider(
                display_name="ChatGPT Produccion",
                provider_type="openai",
                enabled=True,
                is_default=True,
                model="gpt-platform-live",
                encrypted_api_key=encrypt_secret("sk-platform-9999"),
                timeout_seconds=12,
                max_completion_tokens=450,
            )
        )
        session.commit()
        tenant_id = tenant.id

    def fail_post(*_args, **_kwargs):
        raise AssertionError("No debe llamarse al proveedor externo para consultas operativas")

    monkeypatch.setattr("app.application.tenant_chat.httpx.post", fail_post)

    response = client.post(
        "/api/v1/cliente/chat/ask",
        json={"question": "dame   el estado   del comprobante e310000000778"},
        headers=_tenant_headers(tenant_id),
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "local"
    assert "E310000000778" in body["answer"]
    assert body["preprocess"]["dispatchStrategy"] == "local_only"
    assert body["preprocess"]["providerSkippedToSaveCredits"] is True
    assert body["warnings"]
