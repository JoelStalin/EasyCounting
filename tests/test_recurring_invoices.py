from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.main import app
from app.models.base import Base
from app.models.billing import Plan
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.models.user import User
from app.shared.database import get_db
from app.shared.security import create_jwt, hash_password
from app.shared.storage import storage
from app.shared.time import utcnow


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


def _seed_tenant(
    SessionLocal: sessionmaker,
    *,
    plan_name: str = "Profesional",
    includes_recurring_invoices: bool = True,
) -> tuple[int, int]:
    with SessionLocal() as session:
        plan = Plan(
            name=plan_name,
            includes_recurring_invoices=includes_recurring_invoices,
        )
        session.add(plan)
        session.flush()
        tenant = Tenant(
            name="Empresa Recurrente",
            rnc="14151617180",
            env="PRECERT",
            onboarding_status="completed",
            plan_id=plan.id,
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add(tenant)
        session.flush()
        user = User(
            tenant_id=tenant.id,
            email="recurrente@getupsoft.com.do",
            phone="8095550022",
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


def test_client_can_create_and_list_recurring_invoice_schedule(tmp_path: Path) -> None:
    client, SessionLocal = _client_with_sqlite()
    original_base = _with_storage_base(tmp_path)
    try:
        tenant_id, user_id = _seed_tenant(SessionLocal)
        headers = _tenant_headers(user_id, tenant_id)
        start_at = (utcnow() + timedelta(days=1)).isoformat()

        response = client.post(
            "/api/v1/cliente/recurring-invoices",
            json={
                "name": "Factura mensual soporte",
                "frequency": "monthly",
                "startAt": start_at,
                "tipoEcf": "E31",
                "rncReceptor": "101010101",
                "total": "3200.00",
                "notes": "Soporte mensual",
            },
            headers=headers,
        )
        assert response.status_code == 201
        created = response.json()
        assert created["name"] == "Factura mensual soporte"
        assert created["status"] == "active"
        assert created["frequency"] == "monthly"

        listing = client.get("/api/v1/cliente/recurring-invoices", headers=headers)
        assert listing.status_code == 200
        assert len(listing.json()) == 1
    finally:
        storage.base_path = original_base
        app.dependency_overrides.clear()


def test_run_due_recurring_invoices_generates_invoice_and_advance_schedule(tmp_path: Path) -> None:
    client, SessionLocal = _client_with_sqlite()
    original_base = _with_storage_base(tmp_path)
    try:
        tenant_id, user_id = _seed_tenant(SessionLocal)
        headers = _tenant_headers(user_id, tenant_id)
        start_at = (utcnow() - timedelta(minutes=5)).isoformat()

        created = client.post(
            "/api/v1/cliente/recurring-invoices",
            json={
                "name": "Factura diaria monitoreo",
                "frequency": "daily",
                "startAt": start_at,
                "tipoEcf": "E31",
                "total": "900.00",
            },
            headers=headers,
        ).json()

        run_response = client.post("/api/v1/cliente/recurring-invoices/run-due", headers=headers)
        assert run_response.status_code == 200
        summary = run_response.json()
        assert summary["processed"] == 1
        assert summary["generated"] == 1

        listing = client.get("/api/v1/cliente/recurring-invoices", headers=headers)
        schedule = listing.json()[0]
        assert schedule["id"] == created["id"]
        assert schedule["lastGeneratedInvoiceId"] is not None
        assert schedule["nextRunAt"] is not None
        assert len(schedule["executions"]) == 1
        assert schedule["executions"][0]["status"] == "generated"

        with SessionLocal() as session:
            invoice = session.get(Invoice, schedule["lastGeneratedInvoiceId"])
            assert invoice is not None
            assert invoice.estado_dgii == "PROGRAMADA_GENERADA"
    finally:
        storage.base_path = original_base
        app.dependency_overrides.clear()


def test_paused_schedule_is_not_processed_until_resumed(tmp_path: Path) -> None:
    client, SessionLocal = _client_with_sqlite()
    original_base = _with_storage_base(tmp_path)
    try:
        tenant_id, user_id = _seed_tenant(SessionLocal)
        headers = _tenant_headers(user_id, tenant_id)
        start_at = (utcnow() - timedelta(minutes=5)).isoformat()

        created = client.post(
            "/api/v1/cliente/recurring-invoices",
            json={
                "name": "Factura personalizada",
                "frequency": "custom",
                "customIntervalDays": 20,
                "startAt": start_at,
                "tipoEcf": "E31",
                "total": "1800.00",
            },
            headers=headers,
        ).json()

        pause = client.post(f"/api/v1/cliente/recurring-invoices/{created['id']}/pause", headers=headers)
        assert pause.status_code == 200
        assert pause.json()["status"] == "paused"

        run_paused = client.post("/api/v1/cliente/recurring-invoices/run-due", headers=headers)
        assert run_paused.status_code == 200
        assert run_paused.json()["processed"] == 0

        resume = client.post(f"/api/v1/cliente/recurring-invoices/{created['id']}/resume", headers=headers)
        assert resume.status_code == 200
        assert resume.json()["status"] == "active"

        run_active = client.post("/api/v1/cliente/recurring-invoices/run-due", headers=headers)
        assert run_active.status_code == 200
        assert run_active.json()["processed"] == 1
    finally:
        storage.base_path = original_base
        app.dependency_overrides.clear()


def test_basic_plan_cannot_create_recurring_invoice_schedule(tmp_path: Path) -> None:
    client, SessionLocal = _client_with_sqlite()
    original_base = _with_storage_base(tmp_path)
    try:
        tenant_id, user_id = _seed_tenant(
            SessionLocal,
            plan_name="Emprendedor",
            includes_recurring_invoices=False,
        )
        headers = _tenant_headers(user_id, tenant_id)
        start_at = (utcnow() + timedelta(days=1)).isoformat()

        response = client.post(
            "/api/v1/cliente/recurring-invoices",
            json={
                "name": "Factura mensual bloqueada",
                "frequency": "monthly",
                "startAt": start_at,
                "tipoEcf": "E31",
                "total": "3200.00",
            },
            headers=headers,
        )

        assert response.status_code == 403
        assert "Profesional" in response.json()["detail"]
    finally:
        storage.base_path = original_base
        app.dependency_overrides.clear()
