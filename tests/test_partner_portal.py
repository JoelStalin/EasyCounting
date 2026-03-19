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
from app.models.base import Base
from app.models.invoice import Invoice
from app.models.partner import PartnerAccount, PartnerTenantAssignment
from app.models.tenant import Tenant
from app.models.user import User
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


def _partner_headers(user_id: int, role: str) -> dict[str, str]:
    token = create_jwt({"sub": str(user_id), "tenant_id": 1, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_partner_dashboard_lists_only_assigned_tenants() -> None:
    client, SessionLocal = _client_with_sqlite()
    with SessionLocal() as session:
        hub_tenant = Tenant(
            name="Partner Hub",
            rnc="00000000001",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        client_a = Tenant(
            name="Cliente A",
            rnc="12345678901",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        client_b = Tenant(
            name="Cliente B",
            rnc="10987654321",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add_all([hub_tenant, client_a, client_b])
        session.flush()

        account = PartnerAccount(name="Seller Demo", slug="seller-demo")
        session.add(account)
        session.flush()

        user = User(
            tenant_id=hub_tenant.id,
            partner_account_id=account.id,
            email="seller@getupsoft.com.do",
            phone="8095553000",
            password_hash=hash_password("Seller123!"),
            mfa_secret="",
            role="partner_reseller",
            status="activo",
        )
        session.add(user)
        session.flush()

        session.add(
            PartnerTenantAssignment(
                partner_account_id=account.id,
                tenant_id=client_a.id,
                can_emit=True,
                can_manage=True,
            )
        )
        session.add(
            Invoice(
                tenant_id=client_a.id,
                encf="E310000009999",
                tipo_ecf="E31",
                xml_path="/tmp/partner.xml",
                xml_hash="hash-partner",
                estado_dgii="ACEPTADO",
                total=Decimal("1250.00"),
                fecha_emision=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        session.commit()
        user_id = user.id
        client_a_id = client_a.id

    dashboard = client.get("/api/v1/partner/dashboard", headers=_partner_headers(user_id, "partner_reseller"))
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["tenantCount"] == 1
    assert body["invoiceCount"] == 1
    assert body["partner"]["accountSlug"] == "seller-demo"
    assert body["tenants"][0]["id"] == client_a_id

    tenant_list = client.get("/api/v1/partner/tenants", headers=_partner_headers(user_id, "partner_reseller"))
    app.dependency_overrides.clear()
    assert tenant_list.status_code == 200
    assert len(tenant_list.json()) == 1


def test_partner_emit_creates_invoice_for_assigned_tenant() -> None:
    client, SessionLocal = _client_with_sqlite()
    with SessionLocal() as session:
        hub_tenant = Tenant(
            name="Partner Hub",
            rnc="00000000002",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        assigned_tenant = Tenant(
            name="Cliente Emitible",
            rnc="22345678901",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add_all([hub_tenant, assigned_tenant])
        session.flush()

        account = PartnerAccount(name="Seller Operador", slug="seller-operador")
        session.add(account)
        session.flush()

        user = User(
            tenant_id=hub_tenant.id,
            partner_account_id=account.id,
            email="operator@getupsoft.com.do",
            phone="8095553001",
            password_hash=hash_password("Seller123!"),
            mfa_secret="",
            role="partner_operator",
            status="activo",
        )
        session.add(user)
        session.flush()

        session.add(
            PartnerTenantAssignment(
                partner_account_id=account.id,
                tenant_id=assigned_tenant.id,
                can_emit=True,
                can_manage=False,
            )
        )
        session.commit()
        user_id = user.id
        tenant_id = assigned_tenant.id

    response = client.post(
        "/api/v1/partner/emit",
        json={
            "tenantId": tenant_id,
            "encf": "E310000001234",
            "tipoEcf": "E31",
            "rncReceptor": "101010101",
            "total": "2500.00",
        },
        headers=_partner_headers(user_id, "partner_operator"),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["tenantId"] == tenant_id
    assert payload["estadoDgii"] == "SIMULADO"

    with SessionLocal() as session:
        invoice = session.get(Invoice, payload["invoiceId"])
        assert invoice is not None
        assert invoice.tenant_id == tenant_id
        assert invoice.encf == "E310000001234"

    app.dependency_overrides.clear()


def test_partner_auditor_cannot_emit() -> None:
    client, SessionLocal = _client_with_sqlite()
    with SessionLocal() as session:
        hub_tenant = Tenant(
            name="Partner Hub",
            rnc="00000000003",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        assigned_tenant = Tenant(
            name="Cliente Auditado",
            rnc="32345678901",
            env="PRECERT",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add_all([hub_tenant, assigned_tenant])
        session.flush()

        account = PartnerAccount(name="Seller Auditor", slug="seller-auditor")
        session.add(account)
        session.flush()

        user = User(
            tenant_id=hub_tenant.id,
            partner_account_id=account.id,
            email="auditor@getupsoft.com.do",
            phone="8095553002",
            password_hash=hash_password("Seller123!"),
            mfa_secret="",
            role="partner_auditor",
            status="activo",
        )
        session.add(user)
        session.flush()

        session.add(
            PartnerTenantAssignment(
                partner_account_id=account.id,
                tenant_id=assigned_tenant.id,
                can_emit=True,
                can_manage=False,
            )
        )
        session.commit()
        user_id = user.id
        tenant_id = assigned_tenant.id

    response = client.post(
        "/api/v1/partner/emit",
        json={
            "tenantId": tenant_id,
            "encf": "E310000001235",
            "tipoEcf": "E31",
            "rncReceptor": "101010101",
            "total": "999.00",
        },
        headers=_partner_headers(user_id, "partner_auditor"),
    )
    app.dependency_overrides.clear()
    assert response.status_code == 403
    assert "emision" in response.json()["detail"]
