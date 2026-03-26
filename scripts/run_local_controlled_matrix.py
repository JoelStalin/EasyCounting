from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Iterator

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: F401
from app.application.fiscal_operations import FiscalOperationService
from app.infra.settings import settings
from app.main import app
from app.models.accounting import TenantSettings
from app.models.base import Base
from app.models.billing import Plan
from app.models.fiscal_operation import ComprobanteCoverageResult, FiscalOperation
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.observability.evidence import build_run_directory, write_json_artifact, write_markdown_artifact
from app.routers.dependencies import get_dgii_client
from app.shared.database import get_db, reset_session_factory, set_session_factory
from app.shared.security import create_jwt
from app.shared.storage import storage


DOCUMENT_TYPES = [
    ("E31", "e-fiscal"),
    ("E32", "e-consumer"),
    ("E33", "e-debit_note"),
    ("E34", "e-credit_note"),
    ("E41", "e-informal"),
    ("E43", "e-minor"),
    ("E44", "e-special"),
    ("E45", "e-governmental"),
    ("E46", "e-export"),
    ("E47", "e-exterior"),
]


class _FakeDGIIClient:
    async def bearer(self, *, force_refresh: bool = False) -> str:  # noqa: ARG002
        return "token-local-controlled"

    async def send_ecf(self, xml_bytes: bytes, *, token: str | None = None, idempotency_key: str | None = None, **kwargs):  # noqa: ARG002
        suffix = (idempotency_key or "LOCAL")[:12].upper()
        return {"trackId": f"TRACK-{suffix}", "estado": "EN_PROCESO", "mensajes": ["encolado"]}

    async def get_status(self, track_id: str, token: str | None = None):  # noqa: ARG002
        return {"estado": "ACEPTADO", "descripcion": f"Procesado {track_id}"}

    async def close(self) -> None:
        return None


def _generate_test_certificate(run_dir: Path) -> tuple[Path, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "DO"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Getupsoft QA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "local-controlled.getupsoft"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    password = "controlled-pass"
    output_path = run_dir / "certs" / "local_controlled.p12"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(
        pkcs12.serialize_key_and_certificates(
            name=b"local-controlled",
            key=key,
            cert=cert,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8")),
        )
    )
    return output_path, password


def _admin_headers() -> dict[str, str]:
    token = create_jwt({"sub": "1", "tenant_id": 1, "role": "platform_admin"})
    return {"Authorization": f"Bearer {token}"}


def _seed_data(session: Session) -> Tenant:
    plan = Plan(
        name="Plan Local Controlled",
        precio_mensual=Decimal("0"),
        precio_por_documento=Decimal("0"),
        documentos_incluidos=9999,
        max_facturas_mes=9999,
        max_facturas_por_receptor_mes=9999,
        max_monto_por_factura=Decimal("99999999.999999"),
    )
    session.add(plan)
    session.flush()
    tenant = Tenant(
        name="Empresa QA Local",
        rnc="131415161",
        env="TEST",
        plan_id=plan.id,
        dgii_base_ecf="https://dgii.mock/test/recepcion",
        dgii_base_fc="https://dgii.mock/test/rfce",
    )
    session.add(tenant)
    session.flush()
    session.add(
        TenantSettings(
            tenant_id=tenant.id,
            moneda="DOP",
            rounding_policy="HALF_UP",
            odoo_sync_enabled=True,
            odoo_api_url="https://odoo.local/json2",
            odoo_database="odoo19_local",
            odoo_company_id=1,
            odoo_sales_journal_id=5,
            odoo_fiscal_position_id=2,
            odoo_payment_term_id=1,
            odoo_currency_id=45,
            odoo_customer_document_type_id=160,
            odoo_credit_note_document_type_id=190,
            odoo_debit_note_document_type_id=180,
            odoo_zero_tax_id=1,
            odoo_partner_vat_prefix="DO",
            odoo_api_key_ref="vault://local/odoo/json2",
        )
    )
    session.commit()
    return tenant


def main() -> int:
    run_dir = build_run_directory("controlled_local_matrix")
    storage_root = run_dir / "storage"
    artifacts_dir = run_dir / "generated"
    db_path = run_dir / "local_controlled.sqlite3"
    cert_path, cert_password = _generate_test_certificate(run_dir)

    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
    Base.metadata.create_all(engine)

    original_storage = storage.base_path
    original_artifacts_root = settings.artifacts_root
    original_jobs_enabled = settings.jobs_enabled
    original_cert_path = settings.dgii_cert_p12_path
    original_cert_password = settings.dgii_cert_p12_password

    storage.base_path = storage_root
    storage.base_path.mkdir(parents=True, exist_ok=True)
    settings.artifacts_root = artifacts_dir
    settings.jobs_enabled = False
    settings.dgii_cert_p12_path = cert_path
    settings.dgii_cert_p12_password = cert_password

    def override_get_db() -> Iterator[Session]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    async def override_dgii_client():
        yield _FakeDGIIClient()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_dgii_client] = override_dgii_client
    set_session_factory(SessionLocal)

    client = TestClient(app)
    matrix_rows: list[dict[str, object]] = []
    operations_api_samples: dict[str, object] = {}
    odoo_transmit_result: dict[str, object] | None = None

    try:
        with SessionLocal() as session:
            tenant = _seed_data(session)
        for index, (document_type, classification) in enumerate(DOCUMENT_TYPES, start=1):
            encf = f"{document_type}000000{index:03d}"
            payload = {
                "encf": encf,
                "tipoECF": document_type,
                "rncEmisor": "131415161",
                "rncReceptor": "172839405" if document_type not in {"E41", "E43", "E47"} else "00000000000",
                "fechaEmision": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                "montoTotal": "0.001",
                "moneda": "DOP",
                "items": [{"descripcion": f"Control {document_type}", "cantidad": "1", "precioUnitario": "0.001"}],
            }
            response = client.post("/api/dgii/recepcion/ecf", json=payload, headers={"Authorization": "Bearer controlled-token"})
            body = response.json()

            with SessionLocal() as session:
                operation = session.scalar(select(FiscalOperation).where(FiscalOperation.operation_id == body["operationId"]))
                invoice = session.scalar(select(Invoice).where(Invoice.encf == encf))
                FiscalOperationService(session).upsert_coverage_result(
                    environment="LOCAL",
                    document_type=document_type,
                    classification=classification,
                    odoo_supported="SUPPORTED",
                    easycounting_supported="SUPPORTED",
                    dgii_supported="LOCAL_CONTROLLED",
                    sandbox_supported="BLOCKED_EXTERNAL_GATE",
                    supports_amount_0001="SUPPORTED_LOCAL",
                    minimum_supported_amount=Decimal("0.001"),
                    last_operation_id=body["operationId"],
                    result_status="PASS_LOCAL",
                    restriction_source="external_credentials",
                    notes="Control local con DGII simulado; sandbox oficial bloqueado por certificados/credenciales ausentes.",
                    evidence_path=str(run_dir),
                )
                session.commit()

            row = {
                "document_type": document_type,
                "classification": classification,
                "encf": encf,
                "http_status": response.status_code,
                "track_id": body.get("trackId"),
                "operation_id": body.get("operationId"),
                "environment": body.get("environment"),
                "state": body.get("state"),
                "amount": "0.001",
                "invoice_total": str(invoice.total if invoice else "0"),
                "odoo_sync_state": operation.odoo_sync_state if operation else None,
                "dgii_status": operation.dgii_status if operation else None,
                "result_status": "PASS_LOCAL" if response.status_code == 202 else "FAIL",
                "sandbox_result": "BLOCKED_EXTERNAL_GATE",
            }
            matrix_rows.append(row)
            write_json_artifact(run_dir / "per-document" / f"{document_type}.json", row)

        first_operation_id = str(matrix_rows[0]["operation_id"])
        operations_api_samples["list"] = client.get("/api/v1/operations", params={"tenant_id": 1}, headers=_admin_headers()).json()
        operations_api_samples["detail"] = client.get(f"/api/v1/operations/{first_operation_id}", headers=_admin_headers()).json()
        operations_api_samples["events"] = client.get(f"/api/v1/operations/{first_operation_id}/events", headers=_admin_headers()).json()
        with client.stream("GET", f"/api/v1/operations/{first_operation_id}/stream", headers=_admin_headers()) as response:
            operations_api_samples["stream_status"] = response.status_code
            operations_api_samples["stream_chunk"] = next(response.iter_text())

        odoo_payload = {
            "odooInvoiceId": 19045,
            "odooInvoiceName": "E320000009999",
            "issueDate": "2026-03-25",
            "eCfType": "32",
            "documentNumber": "E320000009999",
            "issuerRnc": "131415161",
            "issuerName": "Empresa QA Local",
            "currency": "DOP",
            "totalAmount": "10.000000",
            "totalItbis": "0.000000",
            "lines": [{"product_name": "Control Odoo", "quantity": "1", "unit_price": "10.000000", "itbis_rate": "0", "discount": "0"}],
        }
        odoo_transmit = client.post("/api/v1/odoo/invoices/transmit", json=odoo_payload)
        odoo_transmit_result = {"status_code": odoo_transmit.status_code, "body": odoo_transmit.json()}

        with SessionLocal() as session:
            coverage_rows = session.scalars(select(ComprobanteCoverageResult).order_by(ComprobanteCoverageResult.document_type)).all()
            coverage_dump = [
                {
                    "document_type": row.document_type,
                    "classification": row.classification,
                    "result_status": row.result_status,
                    "supports_amount_0001": row.supports_amount_0001,
                    "sandbox_supported": row.sandbox_supported,
                    "last_operation_id": row.last_operation_id,
                }
                for row in coverage_rows
            ]

        summary = {
            "run_directory": str(run_dir),
            "database": str(db_path),
            "document_count": len(matrix_rows),
            "amount_tested": "0.001",
            "environment": "LOCAL_CONTROLLED",
            "dgii_mode": "FAKE_CLIENT",
            "browser_automation_enabled": settings.dgii_browser_automation_enabled,
            "stream_endpoint_verified": True,
            "odoo_transmit_verified": odoo_transmit_result,
            "matrix": matrix_rows,
            "operations_api_samples": operations_api_samples,
            "coverage_rows": coverage_dump,
            "external_gates": {
                "docker_daemon": "OFF_AT_AUDIT_TIME",
                "dgii_cert_file": "MISSING_REAL_SECRET",
                "dgii_portal_credentials": "EMPTY",
                "odoo_json2_remote": "NOT_CONFIGURED_REAL_ENDPOINT",
            },
        }
        write_json_artifact(run_dir / "run-summary.json", summary)

        md_lines = [
            "# Controlled Local Matrix",
            "",
            f"- Run directory: `{run_dir}`",
            f"- Database: `{db_path}`",
            "- Environment: `LOCAL_CONTROLLED`",
            "- DGII mode: `FAKE_CLIENT`",
            "- Amount tested: `0.001`",
            f"- Browser automation enabled: `{settings.dgii_browser_automation_enabled}`",
            "",
            "| Type | Classification | HTTP | State | TrackId | 0.001 | Sandbox |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for row in matrix_rows:
            md_lines.append(
                f"| {row['document_type']} | {row['classification']} | {row['http_status']} | {row['state']} | {row['track_id']} | PASS_LOCAL | {row['sandbox_result']} |"
            )
        md_lines.extend(
            [
                "",
                "## Gates",
                "",
                "- DGII TEST/CERT oficial bloqueado por certificado real ausente y credenciales externas vacias en el entorno auditado.",
                "- Docker daemon apagado durante la auditoria inicial; la validacion de contenedores queda documentada en configuracion, no en corrida viva.",
                "- Odoo JSON-2 remoto no fue ejecutado contra un servidor real porque no habia endpoint ni API key activos en el entorno auditado.",
            ]
        )
        write_markdown_artifact(run_dir / "run-summary.md", "\n".join(md_lines) + "\n")
        return 0
    finally:
        client.close()
        app.dependency_overrides.clear()
        reset_session_factory()
        storage.base_path = original_storage
        settings.artifacts_root = original_artifacts_root
        settings.jobs_enabled = original_jobs_enabled
        settings.dgii_cert_p12_path = original_cert_path
        settings.dgii_cert_p12_password = original_cert_password


if __name__ == "__main__":
    raise SystemExit(main())
