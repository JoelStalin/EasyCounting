from __future__ import annotations

import base64
from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.main import app
from app.models.base import Base
from app.models.tenant import Tenant
from app.routers.internal import _is_local_internal_host
from app.shared.database import get_db
from app.shared.storage import storage


def _client_with_sqlite(tmp_path: Path) -> tuple[TestClient, sessionmaker]:
    from app.infra.settings import settings

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
    Base.metadata.create_all(engine)

    original_storage = storage.base_path
    storage.base_path = tmp_path / "storage"
    storage.base_path.mkdir(parents=True, exist_ok=True)

    original_jobs = settings.jobs_enabled
    original_environment = settings.environment
    settings.jobs_enabled = False
    settings.environment = "test"

    def override_get_db() -> Iterator[Session]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    client._test_cleanup = (original_storage, original_jobs, original_environment)  # type: ignore[attr-defined]
    return client, SessionLocal


def _cleanup_client(client: TestClient) -> None:
    from app.infra.settings import settings

    original_storage, original_jobs, original_environment = client._test_cleanup  # type: ignore[attr-defined]
    client.close()
    storage.base_path = original_storage
    settings.jobs_enabled = original_jobs
    settings.environment = original_environment
    app.dependency_overrides.clear()


def _seed_tenant(session: Session) -> None:
    tenant = Tenant(
        id=1,
        name="Tenant Certificado",
        rnc="22500706423",
        env="CERT",
        dgii_base_ecf="https://ecf.dgii.gov.do/CerteCF/Recepcion",
        dgii_base_fc="https://fc.dgii.gov.do/certecf/recepcionfc",
    )
    session.add(tenant)
    session.commit()


def test_tenant_can_upload_and_list_active_certificate(tmp_path: Path, certificate_bundle) -> None:
    client, SessionLocal = _client_with_sqlite(tmp_path)
    try:
        with SessionLocal() as session:
            _seed_tenant(session)

        cert_path, password, _key, _cert = certificate_bundle
        with cert_path.open("rb") as certificate_file:
            response = client.post(
                "/api/v1/cliente/certificates",
                data={"alias": "Certificado principal", "password": password.decode(), "activate": "true"},
                files={"certificate": (cert_path.name, certificate_file, "application/x-pkcs12")},
            )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["isActive"] is True
        assert body["alias"] == "Certificado principal"

        listed = client.get("/api/v1/cliente/certificates")
        assert listed.status_code == 200
        listed_body = listed.json()
        assert listed_body["activeSource"] == "tenant"
        assert listed_body["activeCertificateId"] == body["id"]
        assert len(listed_body["items"]) == 1
        assert listed_body["items"][0]["isActive"] is True

        with SessionLocal() as session:
            tenant = session.get(Tenant, 1)
            assert tenant is not None
            assert tenant.cert_ref == str(body["id"])
            assert tenant.p12_kms_key is not None
    finally:
        _cleanup_client(client)


def test_tenant_and_internal_routes_sign_xml_with_active_certificate(tmp_path: Path, certificate_bundle) -> None:
    from app.infra.settings import settings

    client, SessionLocal = _client_with_sqlite(tmp_path)
    try:
        with SessionLocal() as session:
            _seed_tenant(session)

        cert_path, password, _key, _cert = certificate_bundle
        with cert_path.open("rb") as certificate_file:
            upload = client.post(
                "/api/v1/cliente/certificates",
                data={"alias": "Certificado DGII", "password": password.decode(), "activate": "true"},
                files={"certificate": (cert_path.name, certificate_file, "application/x-pkcs12")},
            )
        assert upload.status_code == 201, upload.text

        xml = base64.b64encode(b"<Postulacion><Id>1</Id></Postulacion>").decode("utf-8")
        signed = client.post(
            "/api/v1/cliente/certificates/sign-xml",
            json={"xml": xml, "referenceUri": "", "allowEnvFallback": True},
        )
        assert signed.status_code == 200, signed.text
        signed_body = signed.json()
        assert signed_body["source"] == "tenant"
        decoded_signed = base64.b64decode(signed_body["xmlSigned"]).decode("utf-8")
        assert "Signature" in decoded_signed

        internal = client.post(
            "/api/v1/internal/certificates/sign-xml",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"tenantId": 1, "xml": xml},
        )
        assert internal.status_code == 200, internal.text
        internal_body = internal.json()
        assert internal_body["source"] == "tenant"
        decoded_internal = base64.b64decode(internal_body["xmlSigned"]).decode("utf-8")
        assert "Signature" in decoded_internal
    finally:
        _cleanup_client(client)


def test_internal_host_detection_accepts_docker_bridge_private_addresses() -> None:
    assert _is_local_internal_host("127.0.0.1") is True
    assert _is_local_internal_host("172.17.0.1") is True
    assert _is_local_internal_host("192.168.1.10") is True
    assert _is_local_internal_host("8.8.8.8") is False


def test_internal_route_can_register_certificate_and_then_sign(tmp_path: Path, certificate_bundle) -> None:
    from app.infra.settings import settings

    client, SessionLocal = _client_with_sqlite(tmp_path)
    try:
        with SessionLocal() as session:
            _seed_tenant(session)

        cert_path, password, _key, _cert = certificate_bundle
        with cert_path.open("rb") as certificate_file:
            register = client.post(
                "/api/v1/internal/certificates/register",
                headers={"X-Internal-Secret": settings.hmac_service_secret},
                data={"tenant_rnc": "22500706423", "alias": "Carga interna", "password": password.decode(), "activate": "true"},
                files={"certificate": (cert_path.name, certificate_file, "application/x-pkcs12")},
            )
        assert register.status_code == 201, register.text
        body = register.json()
        assert body["isActive"] is True

        xml = base64.b64encode(b"<Postulacion><RNC>22500706423</RNC></Postulacion>").decode("utf-8")
        signed = client.post(
            "/api/v1/internal/certificates/sign-xml",
            headers={"X-Internal-Secret": settings.hmac_service_secret},
            json={"tenantRnc": "22500706423", "xml": xml},
        )
        assert signed.status_code == 200, signed.text
        signed_body = signed.json()
        assert signed_body["source"] == "tenant"
        assert "Signature" in base64.b64decode(signed_body["xmlSigned"]).decode("utf-8")
    finally:
        _cleanup_client(client)
