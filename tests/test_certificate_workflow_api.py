from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.main import app
from app.models.base import Base
from app.models.certificate_workflow import WorkflowReminder
from app.shared.database import get_db


def _client_with_sqlite(tmp_path: Path) -> tuple[TestClient, sessionmaker]:
    from app.infra.settings import settings

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
    Base.metadata.create_all(engine)

    original_jobs = settings.jobs_enabled
    original_environment = settings.environment
    original_path = settings.psc_workflow_storage_path
    settings.jobs_enabled = False
    settings.environment = "test"
    settings.psc_workflow_storage_path = tmp_path / "expedientes"

    def override_get_db() -> Iterator[Session]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    client._test_cleanup = (original_jobs, original_environment, original_path)  # type: ignore[attr-defined]
    return client, SessionLocal


def _cleanup_client(client: TestClient) -> None:
    from app.infra.settings import settings

    original_jobs, original_environment, original_path = client._test_cleanup  # type: ignore[attr-defined]
    client.close()
    settings.jobs_enabled = original_jobs
    settings.environment = original_environment
    settings.psc_workflow_storage_path = original_path
    app.dependency_overrides.clear()


def test_intake_and_get_case(certificate_bundle, tmp_path: Path) -> None:
    from app.infra.settings import settings

    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        payload = {
            "rnc": "131-23456-7",
            "razon_social": "Empresa Demo SRL",
            "tipo_contribuyente": "juridica",
            "delegado_nombre": "Juan Perez",
            "delegado_identificacion": "00112345678",
            "delegado_correo": "juan@empresa.com",
            "delegado_telefono": "8095551234",
            "delegado_cargo": "Gerente",
            "psc_preferida": "AVANSI",
            "usa_facturador_gratuito": False,
            "ofv_habilitada": True,
            "alta_ncf_habilitada": True,
            "responsable_ti": "ti@empresa.com",
            "responsable_fiscal": "fiscal@empresa.com",
            "ambiente_objetivo": "test",
        }
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json=payload,
        )
        assert intake.status_code == 200, intake.text
        body = intake.json()
        assert body["status"] == "PRECHECK_OK"
        case_id = body["case_id"]

        detail = client.get(
            f"/api/v1/internal/certificate-workflow/{case_id}",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert detail.status_code == 200, detail.text
        detail_body = detail.json()
        assert detail_body["case_id"] == case_id
        assert detail_body["status"] == "PRECHECK_OK"
        assert len(detail_body["events"]) >= 2
    finally:
        _cleanup_client(client)


def test_validate_certificate_persists_result(certificate_bundle, tmp_path: Path) -> None:
    from app.infra.settings import settings

    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]
        cert_path, password, _key, _cert = certificate_bundle
        with cert_path.open("rb") as handle:
            response = client.post(
                f"/api/v1/internal/certificate-workflow/{case_id}/validate-certificate",
                headers={"X-Internal-Secret": settings.hmac_service_secret},
                data={"password": password.decode()},
                files={"certificate": (cert_path.name, handle, "application/x-pkcs12")},
            )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["validation_status"] == "VALID"
        assert body["sha256"]
    finally:
        _cleanup_client(client)


def test_transition_reminder_and_store_secret(certificate_bundle, tmp_path: Path) -> None:
    from app.infra.settings import settings

    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]

        transition = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_SELECTED", "note": "Seleccion de PSC completada"},
        )
        assert transition.status_code == 200, transition.text
        assert transition.json()["status"] == "PSC_SELECTED"

        reminder = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/reminders",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"title": "Completar solicitud en PSC", "hours": 1},
        )
        assert reminder.status_code == 200, reminder.text
        reminder_id = reminder.json()["id"]

        due = client.get(
            "/api/v1/internal/certificate-workflow/reminders/due?limit=10",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert due.status_code == 200, due.text
        assert isinstance(due.json(), list)

        resolved = client.post(
            f"/api/v1/internal/certificate-workflow/reminders/{reminder_id}/resolve",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert resolved.status_code == 200, resolved.text
        assert resolved.json()["status"] == "RESOLVED"

        cert_path, password, _key, _cert = certificate_bundle
        with cert_path.open("rb") as handle:
            secret_store = client.post(
                f"/api/v1/internal/certificate-workflow/{case_id}/store-secret",
                headers={"X-Internal-Secret": settings.hmac_service_secret},
                data={"password": password.decode()},
                files={"certificate": (cert_path.name, handle, "application/x-pkcs12")},
            )
        assert secret_store.status_code == 200, secret_store.text
        assert secret_store.json()["status"] == "SECRET_STORED"
        assert secret_store.json()["secret_ref"].startswith("env://")
    finally:
        _cleanup_client(client)


def test_process_due_reminders_and_reach_ready_for_dgii(certificate_bundle, tmp_path: Path, monkeypatch) -> None:
    from app.infra.settings import settings

    sent: list[tuple[str, str, str | None]] = []

    def _fake_notify(*, case_id: str, title: str, owner_email: str | None) -> None:
        sent.append((case_id, title, owner_email))

    monkeypatch.setattr("app.routers.certificate_workflow.notify_reminder_due", _fake_notify)
    client, SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]

        reminder = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/reminders",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"title": "Recordatorio vencido", "hours": 1},
        )
        assert reminder.status_code == 200
        reminder_id = reminder.json()["id"]

        # Force due reminder.
        with SessionLocal() as session:
            row = session.get(WorkflowReminder, reminder_id)
            assert row is not None
            row.due_at = row.created_at
            session.commit()

        processed = client.post(
            "/api/v1/internal/certificate-workflow/reminders/process-due?limit=10",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert processed.status_code == 200, processed.text
        assert processed.json()["processed"] >= 1
        assert sent and sent[0][0] == case_id

        # Move through status gates to READY_FOR_DGII.
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_SELECTED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "HUMAN_SUBMISSION_PENDING"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "HUMAN_SUBMISSION_DONE"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_UNDER_REVIEW"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_APPROVED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "CERTIFICATE_RECEIVED"},
        )
        cert_path, password, _key, _cert = certificate_bundle
        with cert_path.open("rb") as handle:
            v = client.post(
                f"/api/v1/internal/certificate-workflow/{case_id}/validate-certificate",
                headers={"X-Internal-Secret": settings.hmac_service_secret},
                data={"password": password.decode()},
                files={"certificate": (cert_path.name, handle, "application/x-pkcs12")},
            )
        assert v.status_code == 200
        with cert_path.open("rb") as handle:
            s = client.post(
                f"/api/v1/internal/certificate-workflow/{case_id}/store-secret",
                headers={"X-Internal-Secret": settings.hmac_service_secret},
                data={"password": password.decode()},
                files={"certificate": (cert_path.name, handle, "application/x-pkcs12")},
            )
        assert s.status_code == 200
        ready = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "READY_FOR_DGII"},
        )
        assert ready.status_code == 200, ready.text
        assert ready.json()["status"] == "READY_FOR_DGII"
    finally:
        _cleanup_client(client)


def test_smoke_sign_from_stored_secret_sets_ready(certificate_bundle, tmp_path: Path) -> None:
    from app.infra.settings import settings

    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]
        cert_path, password, _key, _cert = certificate_bundle
        with cert_path.open("rb") as handle:
            store = client.post(
                f"/api/v1/internal/certificate-workflow/{case_id}/store-secret",
                headers={"X-Internal-Secret": settings.hmac_service_secret},
                data={"password": password.decode()},
                files={"certificate": (cert_path.name, handle, "application/x-pkcs12")},
            )
        assert store.status_code == 200, store.text

        smoke = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/smoke-sign",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert smoke.status_code == 200, smoke.text
        smoke_body = smoke.json()
        assert smoke_body["signature_valid"] is True
        assert smoke_body["status"] == "READY_FOR_DGII"
    finally:
        _cleanup_client(client)


def test_dgii_certification_check_simulated_and_live_mocked(tmp_path: Path, monkeypatch) -> None:
    from app.infra.settings import settings

    class _FakeDGIIClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def bearer(self):
            return "fake-token"

        async def consulta_directorio(self, rnc: str, token: str | None = None):
            return {"rnc": rnc, "estado": "ACTIVO", "token": token}

        async def send_ecf(self, xml_bytes: bytes, token: str | None = None, idempotency_key: str | None = None):
            assert xml_bytes
            return {"trackId": "TRK-LIVE-12345", "status": "RECIBIDO"}

    monkeypatch.setattr("app.routers.certificate_workflow.DGIIClient", _FakeDGIIClient)
    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]
        # Move directly to READY_FOR_DGII for this check.
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_SELECTED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "HUMAN_SUBMISSION_PENDING"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "HUMAN_SUBMISSION_DONE"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_UNDER_REVIEW"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_APPROVED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "CERTIFICATE_RECEIVED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "CERTIFICATE_VALIDATED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "SECRET_STORED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "READY_FOR_DGII"},
        )

        sim = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/dgii-certification-check",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert sim.status_code == 200, sim.text
        assert sim.json()["mode"] == "simulated"

        live = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/dgii-certification-check?live=true&transition_to_in_production=true",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert live.status_code == 200, live.text
        body = live.json()
        assert body["mode"] == "live"
        assert body["token_obtained"] is True
        assert body["directory_checked"] is True
        assert body["status"] == "IN_PRODUCTION_USE"
    finally:
        _cleanup_client(client)


def test_submit_test_ecf_simulated_and_live_mocked(certificate_bundle, tmp_path: Path, monkeypatch) -> None:
    from app.infra.settings import settings

    class _FakeDGIIClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def send_ecf(self, xml_bytes: bytes, token: str | None = None, idempotency_key: str | None = None):
            assert xml_bytes
            assert idempotency_key
            return {"track_id": "TRK-LIVE-99999", "estado": "RECIBIDO"}

    monkeypatch.setattr("app.routers.certificate_workflow.DGIIClient", _FakeDGIIClient)
    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]

        cert_path, password, _key, _cert = certificate_bundle
        with cert_path.open("rb") as handle:
            s = client.post(
                f"/api/v1/internal/certificate-workflow/{case_id}/store-secret",
                headers={"X-Internal-Secret": settings.hmac_service_secret},
                data={"password": password.decode()},
                files={"certificate": (cert_path.name, handle, "application/x-pkcs12")},
            )
        assert s.status_code == 200

        ready = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "READY_FOR_DGII"},
        )
        assert ready.status_code == 200

        simulated = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/submit-test-ecf",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert simulated.status_code == 200, simulated.text
        sim_body = simulated.json()
        assert sim_body["mode"] == "simulated"
        assert sim_body["track_id"].startswith("SIM-")

        live = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/submit-test-ecf?live=true&transition_to_in_production=true",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert live.status_code == 200, live.text
        live_body = live.json()
        assert live_body["mode"] == "live"
        assert live_body["track_id"] == "TRK-LIVE-99999"
        assert live_body["status"] == "IN_PRODUCTION_USE"
    finally:
        _cleanup_client(client)


def test_query_track_status_simulated_and_live_mocked(tmp_path: Path, monkeypatch) -> None:
    from app.infra.settings import settings

    class _FakeDGIIClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get_status(self, track_id: str, token: str | None = None):
            return {"estado": "ACEPTADO", "descripcion": f"Track {track_id} procesado"}

    monkeypatch.setattr("app.routers.certificate_workflow.DGIIClient", _FakeDGIIClient)
    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]

        # Persist a TrackId in workflow events using submit-test simulated.
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_SELECTED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "HUMAN_SUBMISSION_PENDING"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "HUMAN_SUBMISSION_DONE"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_UNDER_REVIEW"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "PSC_APPROVED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "CERTIFICATE_RECEIVED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "CERTIFICATE_VALIDATED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "SECRET_STORED"},
        )
        client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/status",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"status": "READY_FOR_DGII"},
        )
        # Add track event directly by calling submit with explicit track simulated path not requiring secret.
        # Use explicit query parameter for simulated status.
        simulated = client.get(
            f"/api/v1/internal/certificate-workflow/{case_id}/track-status?track_id=TRK-SIM-777",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert simulated.status_code == 200, simulated.text
        sim_body = simulated.json()
        assert sim_body["mode"] == "simulated"
        assert sim_body["track_id"] == "TRK-SIM-777"
        assert sim_body["dgii_status"] == "EN_PROCESO"

        live = client.get(
            f"/api/v1/internal/certificate-workflow/{case_id}/track-status?track_id=TRK-LIVE-ABC&live=true",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert live.status_code == 200, live.text
        live_body = live.json()
        assert live_body["mode"] == "live"
        assert live_body["track_id"] == "TRK-LIVE-ABC"
        assert live_body["dgii_status"] == "ACEPTADO"
    finally:
        _cleanup_client(client)


def test_poll_track_status_simulated_and_live_with_transition(tmp_path: Path, monkeypatch) -> None:
    from app.infra.settings import settings

    class _FakeDGIIClient:
        _calls = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get_status(self, track_id: str, token: str | None = None):
            self.__class__._calls += 1
            if self.__class__._calls < 2:
                return {"estado": "EN PROCESO", "descripcion": f"{track_id} pendiente"}
            return {"estado": "ACEPTADO", "descripcion": f"{track_id} aceptado"}

    monkeypatch.setattr("app.routers.certificate_workflow.DGIIClient", _FakeDGIIClient)
    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]
        # Move to READY_FOR_DGII
        for s in [
            "PSC_SELECTED",
            "HUMAN_SUBMISSION_PENDING",
            "HUMAN_SUBMISSION_DONE",
            "PSC_UNDER_REVIEW",
            "PSC_APPROVED",
            "CERTIFICATE_RECEIVED",
            "CERTIFICATE_VALIDATED",
            "SECRET_STORED",
            "READY_FOR_DGII",
        ]:
            client.post(
                f"/api/v1/internal/certificate-workflow/{case_id}/status",
                headers={"X-Internal-Secret": settings.hmac_service_secret},
                json={"status": s},
            )

        simulated = client.get(
            f"/api/v1/internal/certificate-workflow/{case_id}/track-status/poll?track_id=TRK-SIM-111&max_attempts=2&interval_ms=0",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert simulated.status_code == 200, simulated.text
        sim_body = simulated.json()
        assert sim_body["mode"] == "simulated"
        assert sim_body["dgii_status"] == "ACEPTADO"
        assert sim_body["terminal"] is True
        assert sim_body["status"] == "IN_PRODUCTION_USE"

        # Verify explicit live poll in same case path.
        live = client.get(
            f"/api/v1/internal/certificate-workflow/{case_id}/track-status/poll?track_id=TRK-LIVE-222&live=true&max_attempts=3&interval_ms=0",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert live.status_code == 200, live.text
        live_body = live.json()
        assert live_body["mode"] == "live"
        assert live_body["dgii_status"] == "ACEPTADO"
        assert live_body["terminal"] is True
        assert live_body["status"] == "IN_PRODUCTION_USE"
    finally:
        _cleanup_client(client)


def test_process_ready_track_status_endpoint(tmp_path: Path, monkeypatch) -> None:
    from app.infra.settings import settings

    async def _fake_process_ready_cases_track_poll(*, limit: int = 50, live: bool = False) -> int:
        assert limit == 7
        assert live is True
        return 3

    monkeypatch.setattr(
        "app.routers.certificate_workflow.process_ready_cases_track_poll",
        _fake_process_ready_cases_track_poll,
    )

    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        response = client.post(
            "/api/v1/internal/certificate-workflow/track-status/process-ready?live=true&limit=7",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["processed"] == 3
        assert body["mode"] == "live"
        assert body["limit"] == 7
    finally:
        _cleanup_client(client)


def test_execution_checkpoint_progress_and_resume(tmp_path: Path) -> None:
    from app.infra.settings import settings

    client, _SessionLocal = _client_with_sqlite(tmp_path)
    try:
        intake = client.post(
            "/api/v1/internal/certificate-workflow/intake",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "rnc": "131234567",
                "razon_social": "Empresa Demo SRL",
                "tipo_contribuyente": "juridica",
                "delegado_nombre": "Juan Perez",
                "delegado_identificacion": "00112345678",
                "delegado_correo": "juan@empresa.com",
                "delegado_telefono": "8095551234",
                "delegado_cargo": "Gerente",
                "psc_preferida": "AVANSI",
                "usa_facturador_gratuito": False,
                "ofv_habilitada": True,
                "alta_ncf_habilitada": True,
                "responsable_ti": "ti@empresa.com",
                "responsable_fiscal": "fiscal@empresa.com",
                "ambiente_objetivo": "test",
            },
        )
        case_id = intake.json()["case_id"]

        start = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/execution/start",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert start.status_code == 200, start.text
        execution_id = start.json()["execution_id"]

        checkpoint_ok = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/checkpoint",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "execution_id": execution_id,
                "step": "PORTAL_LOGIN",
                "action": "login",
                "result": "OK",
                "details": {"url": "https://dgii.gov.do/OFV/home.aspx"},
            },
        )
        assert checkpoint_ok.status_code == 200, checkpoint_ok.text
        assert checkpoint_ok.json()["last_success_step"] == "PORTAL_LOGIN"

        checkpoint_blocked = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/checkpoint",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={
                "execution_id": execution_id,
                "step": "HUMAN_APPROVAL_PENDING",
                "action": "captcha",
                "result": "FAILED_BLOCKED",
                "error_code": "CAPTCHA_BLOCK",
                "error_message": "Captcha requerido",
            },
        )
        assert checkpoint_blocked.status_code == 200, checkpoint_blocked.text
        assert checkpoint_blocked.json()["status"] == "FAILED_BLOCKED"

        progress = client.get(
            f"/api/v1/internal/certificate-workflow/{case_id}/progress",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert progress.status_code == 200, progress.text
        p = progress.json()
        assert p["execution_id"] == execution_id
        assert p["latest_error_code"] == "CAPTCHA_BLOCK"
        assert p["last_success_step"] == "PORTAL_LOGIN"

        resumed = client.post(
            f"/api/v1/internal/certificate-workflow/{case_id}/resume",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
        )
        assert resumed.status_code == 200, resumed.text
        resumed_body = resumed.json()
        assert resumed_body["status"] == "RUNNING"
        assert resumed_body["current_step"] == "PORTAL_LOGIN"
    finally:
        _cleanup_client(client)
