from __future__ import annotations

from pathlib import Path

from scripts.automation.validate_dgii_p12 import validate


def test_validate_p12_success(certificate_bundle) -> None:
    p12_path, password, _key, _cert = certificate_bundle
    result = validate(file_path=p12_path, password=password.decode())
    assert result.valid is True
    assert result.password_ok is True
    assert result.has_private_key is True
    assert result.subject is not None
    assert result.serial_number is not None


def test_validate_p12_missing_file_returns_structured_error() -> None:
    result = validate(file_path=Path("C:/missing-file-does-not-exist.p12"), password="x")
    assert result.valid is False
    assert result.file_exists is False
    assert result.error == "Archivo no existe"

