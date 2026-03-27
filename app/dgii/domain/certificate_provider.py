from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12


@dataclass(slots=True)
class CertificateConfig:
    p12_path: str
    password: str
    expected_subject: str | None = None
    expected_serial: str | None = None
    expected_rnc: str | None = None


@dataclass(slots=True)
class CertificateMetadata:
    subject: str
    serial: str
    fingerprint_sha1: str
    not_before: datetime
    not_after: datetime


@dataclass(slots=True)
class CertificateContext:
    metadata: CertificateMetadata
    private_key_handle: object
    certificate_handle: object


class CertificateProvider:
    """Load and validate PKCS#12 certificates for DGII signing."""

    def load_certificate(self, config: CertificateConfig) -> CertificateContext:
        path = Path(config.p12_path)
        if not path.exists():
            raise FileNotFoundError(f"No existe certificado: {path}")
        bundle = path.read_bytes()
        private_key, cert, _chain = pkcs12.load_key_and_certificates(bundle, config.password.encode("utf-8"))
        if cert is None:
            raise ValueError("El PKCS#12 no contiene certificado")
        if private_key is None:
            raise ValueError("El PKCS#12 no contiene llave privada")

        # cryptography>=42 exposes *_utc; older versions expose naive datetimes.
        not_before = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before.replace(tzinfo=timezone.utc)
        not_after = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now < not_before or now > not_after:
            raise ValueError("Certificado fuera de vigencia")

        subject = cert.subject.rfc4514_string()
        serial = f"{cert.serial_number:X}"
        fingerprint = cert.fingerprint(hashes.SHA1()).hex().upper()

        if config.expected_subject and config.expected_subject not in subject:
            raise ValueError("Subject de certificado no coincide")
        if config.expected_serial and config.expected_serial.upper() != serial.upper():
            raise ValueError("Serial de certificado no coincide")
        if config.expected_rnc and config.expected_rnc not in subject:
            raise ValueError("RNC esperado no coincide con subject del certificado")

        return CertificateContext(
            metadata=CertificateMetadata(
                subject=subject,
                serial=serial,
                fingerprint_sha1=fingerprint,
                not_before=not_before,
                not_after=not_after,
            ),
            private_key_handle=private_key,
            certificate_handle=cert,
        )
