"""Servicios para carga, activación y uso de certificados DGII por tenant."""
from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from cryptography import x509
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, load_only

from app.infra.settings import settings
from app.models.tenant import Certificate, Tenant
from app.security.audit import append_audit_log
from app.security.xml_dsig import (
    CertificateMetadata as SigningCertificateMetadata,
    SigningOptions,
    XMLDigitalSignatureService,
    XMLSigningError,
)
from app.shared.storage import storage


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _datetime_attr(cert: x509.Certificate, utc_name: str, legacy_name: str) -> datetime:
    utc_value = getattr(cert, utc_name, None)
    if utc_value is not None:
        return _normalize_datetime(utc_value)
    return _normalize_datetime(getattr(cert, legacy_name))


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return cleaned or "certificado"


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt_secret(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def _decrypt_secret(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


def _storage_path_for(relative_or_absolute: str) -> Path:
    raw = Path(relative_or_absolute)
    if raw.is_absolute():
        return raw
    return storage.resolve_path(relative_or_absolute)


@dataclass(slots=True)
class CertificateMetadata:
    subject: str
    issuer: str
    not_before: datetime
    not_after: datetime
    fingerprint_sha256: str


@dataclass(slots=True)
class TenantCertificateRuntime:
    source: Literal["tenant", "env", "windows-store", "external"]
    tenant_id: int | None
    certificate_id: int | None
    alias: str
    subject: str
    issuer: str
    not_before: datetime
    not_after: datetime
    p12_path: Path | None
    password: str | None


def load_pkcs12_metadata(bundle: bytes, password: str | None) -> CertificateMetadata:
    try:
        private_key, cert, _chain = pkcs12.load_key_and_certificates(
            bundle,
            password.encode("utf-8") if password else None,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PKCS#12 invalido o password incorrecto") from exc

    if not private_key or not cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo PKCS#12 no contiene llave privada y certificado utilizables",
        )

    return CertificateMetadata(
        subject=cert.subject.rfc4514_string(),
        issuer=cert.issuer.rfc4514_string(),
        not_before=_datetime_attr(cert, "not_valid_before_utc", "not_valid_before"),
        not_after=_datetime_attr(cert, "not_valid_after_utc", "not_valid_after"),
        fingerprint_sha256=cert.fingerprint(hashes.SHA256()).hex().upper(),
    )


class TenantCertificateService:
    """Gestiona certificados persistidos y firma XML con el certificado activo."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.signing_service = XMLDigitalSignatureService()

    @staticmethod
    def _tenant_runtime_query():
        return select(Tenant).options(
            load_only(
                Tenant.id,
                Tenant.name,
                Tenant.rnc,
                Tenant.env,
                Tenant.dgii_base_ecf,
                Tenant.dgii_base_fc,
                Tenant.cert_ref,
                Tenant.p12_kms_key,
                Tenant.plan_id,
                Tenant.pending_plan_id,
                Tenant.plan_change_requested_at,
                Tenant.plan_change_effective_at,
                Tenant.onboarding_status,
            )
        )

    def _get_tenant(self, tenant_id: int) -> Tenant:
        tenant = self.db.scalar(self._tenant_runtime_query().where(Tenant.id == tenant_id).limit(1))
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        return tenant

    def _get_tenant_by_rnc(self, tenant_rnc: str) -> Tenant:
        tenant = self.db.scalar(self._tenant_runtime_query().where(Tenant.rnc == tenant_rnc).limit(1))
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado para el RNC indicado")
        return tenant

    def _resolve_certificate_ref(self, tenant: Tenant) -> Certificate | None:
        raw_ref = (tenant.cert_ref or "").strip()
        if not raw_ref:
            return None
        if raw_ref.isdigit():
            cert = self.db.get(Certificate, int(raw_ref))
            if cert and cert.tenant_id == tenant.id:
                return cert
        cert = self.db.scalar(
            select(Certificate).where(Certificate.tenant_id == tenant.id, Certificate.alias == raw_ref).limit(1)
        )
        if cert:
            return cert
        return self.db.scalar(
            select(Certificate).where(Certificate.tenant_id == tenant.id, Certificate.p12_path == raw_ref).limit(1)
        )

    def _tenant_certificates_desc(self, tenant_id: int) -> list[Certificate]:
        return list(
            self.db.scalars(
                select(Certificate)
                .where(Certificate.tenant_id == tenant_id)
                .order_by(Certificate.not_after.desc(), Certificate.id.desc())
            ).all()
        )

    def _runtime_from_certificate(self, tenant: Tenant, cert: Certificate) -> TenantCertificateRuntime | None:
        password = _decrypt_secret(tenant.p12_kms_key)
        if not password:
            return None
        path = _storage_path_for(cert.p12_path)
        if not path.exists():
            return None
        return TenantCertificateRuntime(
            source="tenant",
            tenant_id=tenant.id,
            certificate_id=cert.id,
            alias=cert.alias,
            subject=cert.subject,
            issuer=cert.issuer,
            not_before=cert.not_before,
            not_after=cert.not_after,
            p12_path=path,
            password=password,
        )

    def _resolve_env_runtime(self) -> TenantCertificateRuntime | None:
        path = Path(settings.dgii_effective_pfx_path)
        if not path.exists():
            return None
        metadata = load_pkcs12_metadata(path.read_bytes(), settings.dgii_effective_pfx_password)
        return TenantCertificateRuntime(
            source="env",
            tenant_id=None,
            certificate_id=None,
            alias="dgii-env-default",
            subject=metadata.subject,
            issuer=metadata.issuer,
            not_before=metadata.not_before,
            not_after=metadata.not_after,
            p12_path=path,
            password=settings.dgii_effective_pfx_password,
        )

    @staticmethod
    def _metadata_to_runtime(
        metadata: SigningCertificateMetadata,
        *,
        source: Literal["windows-store", "external"],
        tenant_id: int | None = None,
    ) -> TenantCertificateRuntime:
        alias = metadata.thumbprint[-8:] if metadata.thumbprint else source
        normalized_not_before = _normalize_datetime(metadata.not_before)
        normalized_not_after = _normalize_datetime(metadata.not_after)
        return TenantCertificateRuntime(
            source=source,
            tenant_id=tenant_id,
            certificate_id=None,
            alias=f"{source}:{alias}",
            subject=metadata.subject,
            issuer=metadata.issuer,
            not_before=normalized_not_before,
            not_after=normalized_not_after,
            p12_path=None,
            password=None,
        )

    def _build_signing_options(
        self,
        *,
        mode: Literal["pfx", "windows-store", "external"],
        reference_uri: str,
        runtime: TenantCertificateRuntime | None,
    ) -> SigningOptions:
        options = SigningOptions(
            signing_mode=mode,
            reference_uri=reference_uri,
            target_tag=(settings.dgii_sign_target_tag or "").strip() or None,
            validate_after_sign=settings.dgii_validate_signature,
            store_location=settings.dgii_cert_store_location,
            store_name=settings.dgii_cert_store_name,
            thumbprint=(settings.dgii_cert_thumbprint or "").strip() or None,
            pfx_path=settings.dgii_effective_pfx_path,
            pfx_password=settings.dgii_effective_pfx_password,
        )
        if runtime is not None:
            options.pfx_path = str(runtime.p12_path) if runtime.p12_path else None
            options.pfx_password = runtime.password
        return options

    @staticmethod
    def _assert_expected_certificate_identity(metadata: SigningCertificateMetadata) -> None:
        expected_subject = (settings.dgii_cert_expected_subject or "").strip()
        expected_serial = (settings.dgii_cert_expected_serial or "").strip().upper()
        expected_rnc = (settings.dgii_cert_expected_rnc or "").strip()

        if expected_subject and expected_subject not in metadata.subject:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Subject del certificado no coincide con DGII_CERT_EXPECTED_SUBJECT",
            )
        if expected_serial and expected_serial != str(metadata.serial).strip().upper():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Serial del certificado no coincide con DGII_CERT_EXPECTED_SERIAL",
            )
        if expected_rnc and expected_rnc not in metadata.subject:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="RNC esperado no coincide con el certificado activo",
            )

    def list_certificates(self, tenant_id: int) -> dict[str, object]:
        tenant = self._get_tenant(tenant_id)
        active_cert = self._resolve_certificate_ref(tenant)
        items = []
        for cert in self._tenant_certificates_desc(tenant.id):
            items.append(
                {
                    "id": cert.id,
                    "alias": cert.alias,
                    "subject": cert.subject,
                    "issuer": cert.issuer,
                    "notBefore": cert.not_before,
                    "notAfter": cert.not_after,
                    "isActive": bool(active_cert and active_cert.id == cert.id),
                }
            )
        active_source = "tenant" if active_cert is not None else ("env" if self._resolve_env_runtime() else None)
        return {
            "items": items,
            "activeCertificateId": active_cert.id if active_cert else None,
            "activeSource": active_source,
        }

    def upload_certificate(
        self,
        *,
        tenant_id: int,
        alias: str,
        password: str,
        p12_bytes: bytes,
        filename: str | None = None,
        activate: bool = True,
        actor: str = "tenant",
        actor_user_id: int | None = None,
    ) -> dict[str, object]:
        tenant = self._get_tenant(tenant_id)
        if not p12_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo de certificado vacio")

        display_alias = (alias or "").strip() or Path(filename or "certificado.p12").stem or "Certificado DGII"
        metadata = load_pkcs12_metadata(p12_bytes, password)
        existing_cert = self.db.scalar(
            select(Certificate)
            .where(
                Certificate.tenant_id == tenant.id,
                Certificate.subject == metadata.subject,
                Certificate.issuer == metadata.issuer,
                Certificate.not_before == metadata.not_before,
                Certificate.not_after == metadata.not_after,
            )
            .limit(1)
        )
        if existing_cert is not None and _storage_path_for(existing_cert.p12_path).exists():
            should_activate = activate or not (tenant.cert_ref or "").strip()
            if should_activate:
                tenant.cert_ref = str(existing_cert.id)
                tenant.p12_kms_key = _encrypt_secret(password)
                self.db.flush()
            append_audit_log(
                self.db,
                tenant_id=tenant.id,
                actor=actor,
                actor_user_id=actor_user_id,
                action="TENANT_CERTIFICATE_REUSED",
                resource=f"certificate:{existing_cert.id}",
                resource_type="certificate",
                resource_id=str(existing_cert.id),
                decision="ALLOW",
                metadata={
                    "alias": existing_cert.alias,
                    "activate": should_activate,
                    "subject": metadata.subject,
                    "issuer": metadata.issuer,
                    "fingerprintSha256": metadata.fingerprint_sha256,
                },
            )
            return {
                "id": existing_cert.id,
                "alias": existing_cert.alias,
                "subject": existing_cert.subject,
                "issuer": existing_cert.issuer,
                "notBefore": existing_cert.not_before,
                "notAfter": existing_cert.not_after,
                "isActive": should_activate,
                "message": "Certificado ya cargado; se reutilizo para firma automatica.",
            }

        slug = _sanitize_filename(display_alias)
        timestamp = _utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        relative_path = f"tenants/{tenant.id}/certificates/{timestamp}_{slug}.p12"
        storage.store_bytes(relative_path, p12_bytes)

        cert = Certificate(
            tenant_id=tenant.id,
            alias=display_alias,
            p12_path=relative_path,
            not_before=metadata.not_before,
            not_after=metadata.not_after,
            issuer=metadata.issuer,
            subject=metadata.subject,
        )
        self.db.add(cert)
        self.db.flush()

        should_activate = activate or not (tenant.cert_ref or "").strip()
        if should_activate:
            tenant.cert_ref = str(cert.id)
            tenant.p12_kms_key = _encrypt_secret(password)
            self.db.flush()

        append_audit_log(
            self.db,
            tenant_id=tenant.id,
            actor=actor,
            actor_user_id=actor_user_id,
            action="TENANT_CERTIFICATE_UPLOADED",
            resource=f"certificate:{cert.id}",
            resource_type="certificate",
            resource_id=str(cert.id),
            decision="ALLOW",
            metadata={
                "alias": display_alias,
                "activate": should_activate,
                "subject": metadata.subject,
                "issuer": metadata.issuer,
                "fingerprintSha256": metadata.fingerprint_sha256,
            },
        )

        return {
            "id": cert.id,
            "alias": cert.alias,
            "subject": cert.subject,
            "issuer": cert.issuer,
            "notBefore": cert.not_before,
            "notAfter": cert.not_after,
            "isActive": should_activate,
            "message": "Certificado cargado, validado y listo para firma automatica.",
        }

    def resolve_runtime(
        self,
        *,
        tenant_id: int | None = None,
        tenant_rnc: str | None = None,
        allow_env_fallback: bool = True,
    ) -> TenantCertificateRuntime:
        tenant: Tenant | None = None
        if tenant_id is not None:
            tenant = self._get_tenant(tenant_id)
        elif tenant_rnc:
            tenant = self._get_tenant_by_rnc(tenant_rnc)

        if tenant is not None:
            active_cert = self._resolve_certificate_ref(tenant)
            candidates: list[Certificate] = []
            if active_cert is not None:
                candidates.append(active_cert)
            candidates.extend(cert for cert in self._tenant_certificates_desc(tenant.id) if active_cert is None or cert.id != active_cert.id)
            for cert in candidates:
                runtime = self._runtime_from_certificate(tenant, cert)
                if runtime is not None:
                    return runtime
            if not allow_env_fallback:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El tenant no tiene un certificado activo y usable para firmar",
                )

        if allow_env_fallback:
            runtime = self._resolve_env_runtime()
            if runtime is not None:
                return runtime

        if tenant_id is not None or tenant_rnc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No existe un certificado utilizable para el tenant solicitado",
            )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No existe un certificado utilizable para firmar")

    def sign_xml(
        self,
        xml_bytes: bytes,
        *,
        tenant_id: int | None = None,
        tenant_rnc: str | None = None,
        allow_env_fallback: bool = True,
        reference_uri: str = "",
    ) -> tuple[bytes, TenantCertificateRuntime]:
        mode: Literal["pfx", "windows-store", "external"] = settings.dgii_signing_mode
        runtime: TenantCertificateRuntime | None = None
        if mode == "pfx":
            runtime = self.resolve_runtime(
                tenant_id=tenant_id,
                tenant_rnc=tenant_rnc,
                allow_env_fallback=allow_env_fallback,
            )
        options = self._build_signing_options(mode=mode, reference_uri=reference_uri, runtime=runtime)
        try:
            metadata = self.signing_service.get_certificate_metadata(options)
            self._assert_expected_certificate_identity(metadata)
            signed_xml = self.signing_service.sign_xml(xml_bytes, options)
            if runtime is None:
                runtime = self._metadata_to_runtime(
                    metadata,
                    source="windows-store" if mode == "windows-store" else "external",
                    tenant_id=tenant_id,
                )
        except XMLSigningError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        assert runtime is not None
        return signed_xml, runtime

    def sign_dgii_document(
        self,
        xml_bytes: bytes,
        *,
        tenant_id: int | None = None,
        tenant_rnc: str | None = None,
        allow_env_fallback: bool = True,
    ) -> tuple[bytes, TenantCertificateRuntime]:
        return self.sign_xml(
            xml_bytes,
            tenant_id=tenant_id,
            tenant_rnc=tenant_rnc,
            allow_env_fallback=allow_env_fallback,
            reference_uri="",
        )
