from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.dgii.domain.certificate_provider import CertificateConfig, CertificateProvider


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(slots=True)
class ValidationOutput:
    file_exists: bool
    password_ok: bool
    has_private_key: bool
    subject: str | None
    serial_number: str | None
    not_before: str | None
    not_after: str | None
    is_expired: bool
    is_not_yet_valid: bool
    fingerprint_sha1: str | None
    sha256: str | None
    valid: bool
    error: str | None = None


def validate_p12_file(
    *,
    file_path: Path,
    password: str,
    expected_subject: str | None = None,
    expected_serial: str | None = None,
    expected_rnc: str | None = None,
) -> ValidationOutput:
    if not file_path.exists():
        return ValidationOutput(
            file_exists=False,
            password_ok=False,
            has_private_key=False,
            subject=None,
            serial_number=None,
            not_before=None,
            not_after=None,
            is_expired=False,
            is_not_yet_valid=False,
            fingerprint_sha1=None,
            sha256=None,
            valid=False,
            error="Archivo no existe",
        )

    file_sha256 = sha256_file(file_path)
    provider = CertificateProvider()
    try:
        context = provider.load_certificate(
            CertificateConfig(
                p12_path=str(file_path),
                password=password,
                expected_subject=expected_subject,
                expected_serial=expected_serial,
                expected_rnc=expected_rnc,
            )
        )
    except Exception as exc:  # noqa: BLE001
        return ValidationOutput(
            file_exists=True,
            password_ok=False,
            has_private_key=False,
            subject=None,
            serial_number=None,
            not_before=None,
            not_after=None,
            is_expired=False,
            is_not_yet_valid=False,
            fingerprint_sha1=None,
            sha256=file_sha256,
            valid=False,
            error=str(exc),
        )

    now = datetime.now(timezone.utc)
    not_before = context.metadata.not_before
    not_after = context.metadata.not_after
    if not_before.tzinfo is None:
        not_before = not_before.replace(tzinfo=timezone.utc)
    if not_after.tzinfo is None:
        not_after = not_after.replace(tzinfo=timezone.utc)

    is_expired = now > not_after
    is_not_yet_valid = now < not_before

    return ValidationOutput(
        file_exists=True,
        password_ok=True,
        has_private_key=True,
        subject=context.metadata.subject,
        serial_number=context.metadata.serial,
        not_before=not_before.isoformat(),
        not_after=not_after.isoformat(),
        is_expired=is_expired,
        is_not_yet_valid=is_not_yet_valid,
        fingerprint_sha1=context.metadata.fingerprint_sha1,
        sha256=file_sha256,
        valid=not is_expired and not is_not_yet_valid,
        error=None,
    )

