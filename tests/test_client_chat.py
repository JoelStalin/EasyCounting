from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.main import app
from app.infra.settings import settings
from app.models.base import Base
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.shared.database import get_db
from app.shared.security import create_jwt


def _create_tenant(session: Session, name: str, rnc: str) -> Tenant:
    tenant = Tenant(
        name=name,
        rnc=rnc,
        env="PRECERT",
        dgii_base_ecf="https://dgii.mock/precert/recepcion",
        dgii_base_fc="https://dgii.mock/precert/rfce",
    )
    session.add(tenant)
    session.flush()
    return tenant


def _tenant_headers(tenant_id: int) -> dict[str, str]:
    token = create_jwt({"sub": f"user-{tenant_id}", "tenant_id": tenant_id, "role": "tenant_user"})
    return {"Authorization": f"Bearer {token}"}


def _platform_headers() -> dict[str, str]:
    token = create_jwt({"sub": "1", "tenant_id": 1, "role": "platform_admin"})
    return {"Authorization": f"Bearer {token}"}


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
    client = TestClient(app)
    return client, SessionLocal


def test_chatbot_answers_with_tenant_scoped_invoice_data(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "local")
    monkeypatch.setattr(settings, "llm_chat_enabled", True)

    client, SessionLocal = _client_with_sqlite()
    with SessionLocal() as session:
        tenant = _create_tenant(session, "Empresa Chat Uno", "10123456789")
        invoice = Invoice(
            tenant_id=tenant.id,
            encf="E310000000001",
            tipo_ecf="E31",
            xml_path="/tmp/chat-1.xml",
            xml_hash="hash-chat-1",
            estado_dgii="ACEPTADO",
            track_id="TRACK-UNO",
            total=Decimal("1250.00"),
            fecha_emision=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(invoice)
        session.commit()

    response = client.post(
        "/api/v1/cliente/chat/ask",
        json={"question": "Cual es el estado del comprobante E310000000001?"},
        headers=_tenant_headers(tenant.id),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == tenant.id
    assert body["engine"] == "local"
    assert "E310000000001" in body["answer"]
    assert body["sources"][0]["encf"] == "E310000000001"
    assert body["sources"][0]["track_id"] == "TRACK-UNO"


def test_chatbot_does_not_leak_other_tenant_invoice(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "local")
    monkeypatch.setattr(settings, "llm_chat_enabled", True)

    client, SessionLocal = _client_with_sqlite()
    with SessionLocal() as session:
        tenant_a = _create_tenant(session, "Empresa Chat A", "10999999991")
        tenant_b = _create_tenant(session, "Empresa Chat B", "10999999992")
        invoice_a = Invoice(
            tenant_id=tenant_a.id,
            encf="E310000000010",
            tipo_ecf="E31",
            xml_path="/tmp/chat-a.xml",
            xml_hash="hash-chat-a",
            estado_dgii="ACEPTADO",
            total=Decimal("100.00"),
            fecha_emision=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        invoice_b = Invoice(
            tenant_id=tenant_b.id,
            encf="E310000000999",
            tipo_ecf="E31",
            xml_path="/tmp/chat-b.xml",
            xml_hash="hash-chat-b",
            estado_dgii="RECHAZADO",
            total=Decimal("999.00"),
            fecha_emision=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add_all([invoice_a, invoice_b])
        session.commit()

    response = client.post(
        "/api/v1/cliente/chat/ask",
        json={"question": "Dame detalles del comprobante E310000000999"},
        headers=_tenant_headers(tenant_a.id),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert "E310000000999" in body["answer"]
    assert "tenant autenticado" in body["answer"]
    assert all(source["encf"] != "E310000000999" for source in body["sources"])
    assert "E310000000010" not in body["answer"]


def test_chatbot_rejects_platform_scope(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "local")
    monkeypatch.setattr(settings, "llm_chat_enabled", True)

    client, _SessionLocal = _client_with_sqlite()
    response = client.post(
        "/api/v1/cliente/chat/ask",
        json={"question": "Resumen de mis comprobantes"},
        headers=_platform_headers(),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 403
