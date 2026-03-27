from __future__ import annotations

import pytest

from app.dgii.domain.certificate_provider import CertificateConfig, CertificateProvider


def test_certificate_provider_loads_valid_p12(certificate_bundle) -> None:
    p12_path, password, _key, _cert = certificate_bundle
    provider = CertificateProvider()
    context = provider.load_certificate(CertificateConfig(p12_path=str(p12_path), password=password.decode()))
    assert context.metadata.subject
    assert context.metadata.serial
    assert len(context.metadata.fingerprint_sha1) == 40


def test_certificate_provider_rejects_wrong_password(certificate_bundle) -> None:
    p12_path, _password, _key, _cert = certificate_bundle
    provider = CertificateProvider()
    with pytest.raises(Exception):
        provider.load_certificate(CertificateConfig(p12_path=str(p12_path), password="wrong-password"))


def test_certificate_provider_rejects_expected_subject_mismatch(certificate_bundle) -> None:
    p12_path, password, _key, _cert = certificate_bundle
    provider = CertificateProvider()
    with pytest.raises(ValueError):
        provider.load_certificate(
            CertificateConfig(
                p12_path=str(p12_path),
                password=password.decode(),
                expected_subject="CN=SUBJECT-INEXISTENTE",
            )
        )
