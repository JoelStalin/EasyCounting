from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.security.xml_dsig import (
    CertificateNotFoundError,
    CertificatePasswordError,
    ExternalSignerNotConfiguredError,
    SigningOptions,
    ThumbprintInvalidError,
    XMLDigitalSignatureService,
    validate_signed_xml,
)
from app.dgii.domain.xml_signature_verification_service import XmlSignatureVerificationService


def _sample_xml() -> bytes:
    return b"<ECF><eNCF>E310000000001</eNCF><MontoTotal>1.00</MontoTotal></ECF>"


def test_sign_xml_with_pfx_generates_dgii_profile_signature(certificate_bundle) -> None:
    p12_path, password, _key, _cert = certificate_bundle
    service = XMLDigitalSignatureService()
    options = SigningOptions(
        signing_mode="pfx",
        pfx_path=str(p12_path),
        pfx_password=password.decode(),
        reference_uri="",
        target_tag="ECF",
        validate_after_sign=True,
    )

    signed = service.sign_xml(_sample_xml(), options)
    assert b"<ds:Signature" in signed or b"<Signature" in signed
    assert b"http://www.w3.org/2001/04/xmldsig-more#rsa-sha256" in signed
    assert b"http://www.w3.org/2001/04/xmlenc#sha256" in signed
    assert b"http://www.w3.org/TR/2001/REC-xml-c14n-20010315" in signed
    assert b'URI=""' in signed
    assert b"<ds:X509Certificate>" in signed or b"<X509Certificate>" in signed

    result = validate_signed_xml(signed)
    assert result.valid is True


def test_sign_xml_with_pfx_invalid_password_raises(certificate_bundle) -> None:
    p12_path, _password, _key, _cert = certificate_bundle
    service = XMLDigitalSignatureService()
    options = SigningOptions(
        signing_mode="pfx",
        pfx_path=str(p12_path),
        pfx_password="bad-password",
        reference_uri="",
    )

    with pytest.raises(CertificatePasswordError):
        service.sign_xml(_sample_xml(), options)


def test_sign_xml_with_pfx_missing_certificate_raises() -> None:
    service = XMLDigitalSignatureService()
    options = SigningOptions(
        signing_mode="pfx",
        pfx_path=str(Path("missing-cert.p12")),
        pfx_password="test",
    )
    with pytest.raises(CertificateNotFoundError):
        service.sign_xml(_sample_xml(), options)


def test_external_signer_mode_is_supported_but_not_implemented() -> None:
    service = XMLDigitalSignatureService()
    with pytest.raises(ExternalSignerNotConfiguredError):
        service.sign_xml(_sample_xml(), SigningOptions(signing_mode="external"))


def test_windows_store_signer_selection_and_signing_is_mockable(monkeypatch, certificate_bundle, tmp_path: Path) -> None:
    p12_path, password, _key, _cert = certificate_bundle
    service = XMLDigitalSignatureService()

    signed_reference = service.sign_xml(
        _sample_xml(),
        SigningOptions(
            signing_mode="pfx",
            pfx_path=str(p12_path),
            pfx_password=password.decode(),
            reference_uri="",
            validate_after_sign=True,
        ),
    )

    thumbprint = "A" * 40

    from app.security import xml_dsig as xml_dsig_module

    def _fake_require_windows(self) -> None:  # noqa: ANN001
        return None

    def _fake_run(self, args: list[str]) -> subprocess.CompletedProcess[str]:  # noqa: ANN001
        if "list_windows_signing_certificates.ps1" in " ".join(args):
            payload = {
                "total": 1,
                "certificates": [
                    {
                        "subject": "CN=Representante DGII",
                        "issuer": "CN=CA DGII",
                        "thumbprint": thumbprint,
                        "not_before": "2025-01-01T00:00:00+00:00",
                        "not_after": "2030-01-01T00:00:00+00:00",
                    }
                ],
            }
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")
        output_index = args.index("-OutputPath") + 1
        out_path = Path(args[output_index])
        out_path.write_bytes(signed_reference)
        payload = {
            "status": "ok",
            "thumbprint": thumbprint,
            "subject": "CN=Representante DGII",
            "issuer": "CN=CA DGII",
            "not_before": "2025-01-01T00:00:00+00:00",
            "not_after": "2030-01-01T00:00:00+00:00",
        }
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(xml_dsig_module.WindowsCertStoreSigner, "_require_windows", _fake_require_windows)
    monkeypatch.setattr(xml_dsig_module.WindowsCertStoreSigner, "_run_powershell", _fake_run)

    options = SigningOptions(
        signing_mode="windows-store",
        thumbprint=thumbprint,
        store_location="CurrentUser",
        store_name="My",
        validate_after_sign=True,
        output_path=str(tmp_path / "signed.xml"),
    )
    signed = service.sign_xml(_sample_xml(), options)
    assert signed == signed_reference
    assert (tmp_path / "signed.xml").exists()

    metadata = service.get_certificate_metadata(options)
    assert metadata.thumbprint == thumbprint
    assert "Representante DGII" in metadata.subject


def test_windows_store_thumbprint_format_validation(monkeypatch) -> None:
    service = XMLDigitalSignatureService()
    from app.security import xml_dsig as xml_dsig_module

    monkeypatch.setattr(xml_dsig_module.WindowsCertStoreSigner, "_require_windows", lambda self: None)
    with pytest.raises(ThumbprintInvalidError):
        service.get_certificate_metadata(
            SigningOptions(signing_mode="windows-store", thumbprint="NOT-HEX")
        )


def test_domain_verification_service_reports_valid_signature(certificate_bundle) -> None:
    p12_path, password, _key, _cert = certificate_bundle
    signing_service = XMLDigitalSignatureService()
    signed = signing_service.sign_xml(
        _sample_xml(),
        SigningOptions(
            signing_mode="pfx",
            pfx_path=str(p12_path),
            pfx_password=password.decode(),
            reference_uri="",
            validate_after_sign=True,
        ),
    )
    result = XmlSignatureVerificationService().verify_signature(signed)
    assert result.valid is True
