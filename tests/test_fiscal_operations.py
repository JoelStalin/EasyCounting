from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.main import app
from app.models.base import Base
from app.models.billing import Plan
from app.models.fiscal_operation import EvidenceArtifact, FiscalOperation, FiscalOperationEvent
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.routers.dependencies import get_dgii_client
from app.shared.database import get_db, reset_session_factory, set_session_factory
from app.shared.security import create_jwt
from app.shared.storage import storage


class _FakeDGIIClient:
    async def bearer(self, *, force_refresh: bool = False) -> str:  # noqa: ARG002
        return "token-test"

    async def send_ecf(self, xml_bytes: bytes, *, token: str | None = None, idempotency_key: str | None = None, **kwargs):  # noqa: ARG002
        return {"trackId": "TRACK-001", "estado": "EN_PROCESO", "mensajes": ["encolado"]}

    async def get_status(self, track_id: str, token: str | None = None):  # noqa: ARG002
        return {"estado": "ACEPTADO", "descripcion": "Procesado"}

    async def close(self) -> None:
        return None

    async def __aenter__(self) -> "_FakeDGIIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()


def _admin_headers() -> dict[str, str]:
    token = create_jwt({"sub": "1", "tenant_id": 1, "role": "platform_admin"})
    return {"Authorization": f"Bearer {token}"}


def _seed_tenant(session: Session) -> Tenant:
    plan = Plan(
        name="Plan QA",
        precio_mensual=Decimal("0"),
        precio_por_documento=Decimal("0"),
        documentos_incluidos=999,
        max_facturas_mes=999,
        max_facturas_por_receptor_mes=999,
        max_monto_por_factura=Decimal("999999.99"),
    )
    session.add(plan)
    session.flush()
    tenant = Tenant(
        name="Empresa QA",
        rnc="131415161",
        env="TEST",
        plan_id=plan.id,
        dgii_base_ecf="https://dgii.mock/test/recepcion",
        dgii_base_fc="https://dgii.mock/test/rfce",
    )
    session.add(tenant)
    session.commit()
    return tenant


def _client_with_sqlite(tmp_path: Path) -> tuple[TestClient, sessionmaker]:
    from app.infra.settings import settings

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
    Base.metadata.create_all(engine)

    storage_root = tmp_path / "storage"
    artifacts_root = tmp_path / "artifacts"
    original_storage = storage.base_path
    original_artifacts = settings.artifacts_root
    original_jobs = settings.jobs_enabled
    storage.base_path = storage_root
    storage.base_path.mkdir(parents=True, exist_ok=True)
    settings.artifacts_root = artifacts_root
    settings.jobs_enabled = False

    def override_get_db() -> Iterator[Session]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    async def override_dgii_client() -> AsyncIterator[_FakeDGIIClient]:
        client = _FakeDGIIClient()
        yield client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_dgii_client] = override_dgii_client
    set_session_factory(SessionLocal)
    client = TestClient(app)
    client._test_cleanup = (original_storage, original_artifacts, original_jobs)  # type: ignore[attr-defined]
    return client, SessionLocal


def _cleanup_client(client: TestClient) -> None:
    from app.infra.settings import settings

    original_storage, original_artifacts, original_jobs = client._test_cleanup  # type: ignore[attr-defined]
    client.close()
    storage.base_path = original_storage
    settings.artifacts_root = original_artifacts
    settings.jobs_enabled = original_jobs
    reset_session_factory()
    app.dependency_overrides.clear()


def test_submit_ecf_creates_operation_invoice_and_evidence(tmp_path: Path, configured_settings) -> None:  # noqa: ARG001
    client, SessionLocal = _client_with_sqlite(tmp_path)
    try:
        with SessionLocal() as session:
            tenant = _seed_tenant(session)
        payload = {
            "encf": "E310000000001",
            "tipoECF": "E31",
            "rncEmisor": "131415161",
            "rncReceptor": "172839405",
            "fechaEmision": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "montoTotal": "0.001",
            "moneda": "DOP",
            "items": [{"descripcion": "Prueba minima", "cantidad": "1", "precioUnitario": "0.001"}],
        }
        response = client.post("/api/dgii/recepcion/ecf", json=payload, headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 202
        body = response.json()
        assert body["trackId"] == "TRACK-001"
        assert body["operationId"]

        with SessionLocal() as session:
            operation = session.scalar(select(FiscalOperation).where(FiscalOperation.operation_id == body["operationId"]))
            assert operation is not None
            assert operation.dgii_track_id == "TRACK-001"
            assert operation.state == "TRACKID_REGISTERED"
            invoice = session.scalar(select(Invoice).where(Invoice.encf == "E310000000001"))
            assert invoice is not None
            assert Decimal(str(invoice.total)) == Decimal("0.001")
            assert invoice.last_operation_id == operation.id
            events = session.scalars(select(FiscalOperationEvent).where(FiscalOperationEvent.operation_fk == operation.id)).all()
            assert any(event.status == "VALIDATING" for event in events)
            assert any(event.status == "TRACKID_REGISTERED" for event in events)
            evidence = session.scalars(select(EvidenceArtifact).where(EvidenceArtifact.operation_fk == operation.id)).all()
            assert len(evidence) >= 2
            assert any(item.artifact_type == "dgii_response" for item in evidence)
            assert tenant.id == operation.tenant_id
    finally:
        _cleanup_client(client)


def test_operations_endpoints_return_detail_and_events(tmp_path: Path, configured_settings) -> None:  # noqa: ARG001
    client, SessionLocal = _client_with_sqlite(tmp_path)
    try:
        with SessionLocal() as session:
            _seed_tenant(session)
        payload = {
            "encf": "E320000000002",
            "tipoECF": "E32",
            "rncEmisor": "131415161",
            "rncReceptor": "00000000000",
            "fechaEmision": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "montoTotal": "1.250000",
            "moneda": "DOP",
            "items": [{"descripcion": "Consumo QA", "cantidad": "1", "precioUnitario": "1.250000"}],
        }
        send = client.post("/api/dgii/recepcion/ecf", json=payload, headers={"Authorization": "Bearer test-token"})
        operation_id = send.json()["operationId"]

        listed = client.get("/api/v1/operations", params={"tenant_id": 1}, headers=_admin_headers())
        assert listed.status_code == 200
        assert listed.json()["total"] >= 1

        detail = client.get(f"/api/v1/operations/{operation_id}", headers=_admin_headers())
        assert detail.status_code == 200
        assert detail.json()["operation_id"] == operation_id
        assert len(detail.json()["events"]) >= 1

        events = client.get(f"/api/v1/operations/{operation_id}/events", headers=_admin_headers())
        assert events.status_code == 200
        assert any(event["status"] == "TRACKID_REGISTERED" for event in events.json())
    finally:
        _cleanup_client(client)


def test_operations_stream_emits_sse_payload(tmp_path: Path, configured_settings) -> None:  # noqa: ARG001
    client, SessionLocal = _client_with_sqlite(tmp_path)
    try:
        with SessionLocal() as session:
            _seed_tenant(session)
        payload = {
            "encf": "E330000000003",
            "tipoECF": "E33",
            "rncEmisor": "131415161",
            "rncReceptor": "172839405",
            "fechaEmision": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "montoTotal": "5.000000",
            "moneda": "DOP",
            "items": [{"descripcion": "Factura QA", "cantidad": "1", "precioUnitario": "5.000000"}],
        }
        send = client.post("/api/dgii/recepcion/ecf", json=payload, headers={"Authorization": "Bearer test-token"})
        operation_id = send.json()["operationId"]

        with client.stream("GET", f"/api/v1/operations/{operation_id}/stream", headers=_admin_headers()) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            chunk = next(response.iter_text())
            assert "operation_event" in chunk or "keep-alive" in chunk
    finally:
        _cleanup_client(client)


def test_odoo_transmit_route_reuses_durable_dgii_pipeline(tmp_path: Path, configured_settings) -> None:  # noqa: ARG001
    client, SessionLocal = _client_with_sqlite(tmp_path)
    try:
        with SessionLocal() as session:
            _seed_tenant(session)
        payload = {
            "odooInvoiceId": 19045,
            "odooInvoiceName": "E320000000045",
            "issueDate": "2026-03-25",
            "eCfType": "32",
            "documentNumber": "E320000000045",
            "issuerRnc": "131415161",
            "issuerName": "Empresa QA",
            "currency": "DOP",
            "totalAmount": "10.000000",
            "totalItbis": "0.000000",
            "lines": [
                {
                    "product_name": "Hamburguesa Chefalita",
                    "quantity": "1",
                    "unit_price": "10.000000",
                    "itbis_rate": "0",
                    "discount": "0",
                }
            ],
        }
        response = client.post("/api/v1/odoo/invoices/transmit", json=payload)
        assert response.status_code == 202
        body = response.json()
        assert body["certia_track_id"] == "TRACK-001"
        assert body["operation_id"]
    finally:
        _cleanup_client(client)
