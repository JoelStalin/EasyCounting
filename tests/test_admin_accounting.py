from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.main import app
from app.db import get_sync_session
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.models.accounting import InvoiceLedgerEntry, TenantSettings
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


def _clear_tables() -> None:
    with get_sync_session() as session:
        for model in (InvoiceLedgerEntry, TenantSettings, Invoice, Tenant):
            session.execute(delete(model))


def _admin_headers() -> dict[str, str]:
    token = create_jwt({"sub": "1", "tenant_id": 1, "role": "platform_admin"})
    return {"Authorization": f"Bearer {token}"}


def test_accounting_summary_returns_totals() -> None:
    _clear_tables()
    with get_sync_session() as session:
        tenant = _create_tenant(session, "Empresa Demo", "12345678901")
        invoices = [
            Invoice(tenant_id=tenant.id, encf="E3100001", tipo_ecf="E31", xml_path="/tmp/a.xml", xml_hash="hash1", estado_dgii="ACEPTADO", total=Decimal("1000.00"), contabilizado=True, accounted_at=datetime.now(timezone.utc).replace(tzinfo=None), asiento_referencia="AS-001"),
            Invoice(tenant_id=tenant.id, encf="E3100002", tipo_ecf="E31", xml_path="/tmp/b.xml", xml_hash="hash2", estado_dgii="RECHAZADO", total=Decimal("500.00")),
            Invoice(tenant_id=tenant.id, encf="E3100003", tipo_ecf="E31", xml_path="/tmp/c.xml", xml_hash="hash3", estado_dgii="ACEPTADO", total=Decimal("250.00")),
        ]
        session.add_all(invoices)
        session.commit()

    client = TestClient(app)
    response = client.get(
        f"/api/admin/tenants/{tenant.id}/accounting/summary",
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["totales"]["total_emitidos"] == 3
    assert data["totales"]["total_aceptados"] == 2
    assert data["contabilidad"]["contabilizados"] == 1


def test_create_ledger_entry_marks_invoice() -> None:
    _clear_tables()
    with get_sync_session() as session:
        tenant = _create_tenant(session, "Empresa Ledger", "10987654321")
        invoice = Invoice(
            tenant_id=tenant.id,
            encf="E3200001",
            tipo_ecf="E32",
            xml_path="/tmp/invoice.xml",
            xml_hash="hash-ledger",
            estado_dgii="ACEPTADO",
            total=Decimal("750.00"),
        )
        session.add(invoice)
        session.commit()

    client = TestClient(app)
    payload = {
        "invoiceId": invoice.id,
        "referencia": "AS-2024-001",
        "cuenta": "401-ING",
        "descripcion": "Registro de ingreso",
        "debit": "0",
        "credit": "750.00",
        "fecha": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }
    response = client.post(
        f"/api/admin/tenants/{tenant.id}/accounting/ledger",
        json=payload,
        headers=_admin_headers(),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["invoiceId"] == invoice.id
    assert body["referencia"] == "AS-2024-001"

    with get_sync_session() as session:
        updated_invoice = session.get(Invoice, invoice.id)
        assert updated_invoice is not None
        assert updated_invoice.contabilizado is True
        assert updated_invoice.asiento_referencia == "AS-2024-001"


def test_update_tenant_settings_roundtrip() -> None:
    _clear_tables()
    with get_sync_session() as session:
        tenant = _create_tenant(session, "Empresa Config", "10293847561")

    client = TestClient(app)
    payload = {
        "moneda": "USD",
        "cuenta_ingresos": "701-VENT",
        "cuenta_itbis": "208-ITBIS",
        "cuenta_retenciones": "209-RET",
        "dias_credito": 30,
        "correo_facturacion": "facturas@empresa.do",
        "telefono_contacto": "+1-809-555-0000",
        "notas": "Config inicial",
    }
    response = client.put(
        f"/api/admin/tenants/{tenant.id}/settings",
        json=payload,
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["moneda"] == "USD"
    assert data["cuenta_ingresos"] == "701-VENT"

    get_response = client.get(
        f"/api/admin/tenants/{tenant.id}/settings",
        headers=_admin_headers(),
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["correo_facturacion"] == "facturas@empresa.do"
