from __future__ import annotations

from pathlib import Path
from typing import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.main import app
from app.models.base import Base
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.models.user import User
from app.shared.database import get_db
from app.shared.security import create_jwt, hash_password
from app.shared.storage import storage


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


def _tenant_headers(user_id: int, tenant_id: int) -> dict[str, str]:
    token = create_jwt({"sub": str(user_id), "tenant_id": tenant_id, "role": "tenant_user"})
    return {"Authorization": f"Bearer {token}"}


def _seed_tenant(SessionLocal: sessionmaker, *, onboarding_status: str = "completed") -> tuple[int, int]:
    with SessionLocal() as session:
        tenant = Tenant(
            name="Empresa API",
            rnc="13141516190" if onboarding_status == "completed" else "13141516191",
            env="PRECERT",
            onboarding_status=onboarding_status,
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add(tenant)
        session.flush()
        user = User(
            tenant_id=tenant.id,
            email="erp@getupsoft.com.do",
            phone="8095550011",
            password_hash=hash_password("Tenant123!"),
            mfa_secret="",
            role="tenant_user",
            status="activo",
        )
        session.add(user)
        session.commit()
        return tenant.id, user.id


def _with_storage_base(tmp_path: Path):
    original = storage.base_path
    storage.base_path = tmp_path
    storage.base_path.mkdir(parents=True, exist_ok=True)
    return original


def test_tenant_user_can_create_list_and_revoke_api_tokens(tmp_path: Path) -> None:
    client, SessionLocal = _client_with_sqlite()
    original_base = _with_storage_base(tmp_path)
    try:
        tenant_id, user_id = _seed_tenant(SessionLocal)
        headers = _tenant_headers(user_id, tenant_id)

        create_response = client.post(
            "/api/v1/cliente/api-tokens",
            json={"name": "Odoo principal", "accessMode": "read_write", "expiresInDays": 365},
            headers=headers,
        )
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["name"] == "Odoo principal"
        assert created["token"].startswith("gtu_tnt_")
        assert created["scopes"] == ["invoices:read", "invoices:write"]

        list_response = client.get("/api/v1/cliente/api-tokens", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        revoke_response = client.delete(f"/api/v1/cliente/api-tokens/{created['id']}", headers=headers)
        assert revoke_response.status_code == 200
        assert revoke_response.json()["revokedAt"] is not None
    finally:
        storage.base_path = original_base
        app.dependency_overrides.clear()


def test_tenant_api_token_can_read_and_register_invoices(tmp_path: Path) -> None:
    client, SessionLocal = _client_with_sqlite()
    original_base = _with_storage_base(tmp_path)
    try:
        tenant_id, user_id = _seed_tenant(SessionLocal)
        headers = _tenant_headers(user_id, tenant_id)
        token_response = client.post(
            "/api/v1/cliente/api-tokens",
            json={"name": "Odoo sync", "accessMode": "read_write", "expiresInDays": 30},
            headers=headers,
        )
        raw_token = token_response.json()["token"]
        api_headers = {"Authorization": f"Bearer {raw_token}"}

        empty_list = client.get("/api/v1/tenant-api/invoices", headers=api_headers)
        assert empty_list.status_code == 200
        assert empty_list.json()["total"] == 0

        create_invoice = client.post(
            "/api/v1/tenant-api/invoices",
            json={
                "encf": "E310000001111",
                "tipoEcf": "E31",
                "rncReceptor": "101010101",
                "total": "2500.00",
            },
            headers=api_headers,
        )
        assert create_invoice.status_code == 201
        created = create_invoice.json()
        assert created["estadoDgii"] == "REGISTRADO_API"

        detail = client.get(f"/api/v1/tenant-api/invoices/{created['invoiceId']}", headers=api_headers)
        assert detail.status_code == 200
        assert detail.json()["encf"] == "E310000001111"

        with SessionLocal() as session:
            invoice = session.get(Invoice, created["invoiceId"])
            assert invoice is not None
            assert invoice.tenant_id == tenant_id
            assert (tmp_path / f"tenant-api/{tenant_id}/E310000001111.json").exists()
    finally:
        storage.base_path = original_base
        app.dependency_overrides.clear()


def test_read_only_token_cannot_register_invoices(tmp_path: Path) -> None:
    client, SessionLocal = _client_with_sqlite()
    original_base = _with_storage_base(tmp_path)
    try:
        tenant_id, user_id = _seed_tenant(SessionLocal)
        headers = _tenant_headers(user_id, tenant_id)
        token_response = client.post(
            "/api/v1/cliente/api-tokens",
            json={"name": "Solo lectura", "accessMode": "read", "expiresInDays": 90},
            headers=headers,
        )
        raw_token = token_response.json()["token"]

        response = client.post(
            "/api/v1/tenant-api/invoices",
            json={
                "encf": "E310000001112",
                "tipoEcf": "E31",
                "rncReceptor": "101010101",
                "total": "999.00",
            },
            headers={"Authorization": f"Bearer {raw_token}"},
        )
        assert response.status_code == 403
        assert "Scope insuficiente" in response.json()["detail"]
    finally:
        storage.base_path = original_base
        app.dependency_overrides.clear()


def test_pending_onboarding_tenant_cannot_register_invoices_via_api(tmp_path: Path) -> None:
    client, SessionLocal = _client_with_sqlite()
    original_base = _with_storage_base(tmp_path)
    try:
        tenant_id, user_id = _seed_tenant(SessionLocal, onboarding_status="pending_fiscal_setup")
        headers = _tenant_headers(user_id, tenant_id)
        token_response = client.post(
            "/api/v1/cliente/api-tokens",
            json={"name": "Odoo preliminar", "accessMode": "read_write", "expiresInDays": 90},
            headers=headers,
        )
        raw_token = token_response.json()["token"]

        response = client.post(
            "/api/v1/tenant-api/invoices",
            json={
                "encf": "E310000001113",
                "tipoEcf": "E31",
                "rncReceptor": "101010101",
                "total": "1800.00",
            },
            headers={"Authorization": f"Bearer {raw_token}"},
        )
        assert response.status_code == 409
        assert "setup fiscal" in response.json()["detail"]
    finally:
        storage.base_path = original_base
        app.dependency_overrides.clear()
