"""Backward-compatible signing helpers backed by the DGII XMLDSIG service."""
from __future__ import annotations

from typing import Optional

from app.infra.settings import settings
from app.security.xml_dsig import (
    CanonicalizationError,
    CertificateExpiredError,
    CertificateMetadata,
    CertificateNotFoundError,
    CertificatePasswordError,
    CertificatePrivateKeyError,
    ExternalSignerNotConfiguredError,
    PfxFileSigner,
    SignatureValidationError,
    SignatureValidationResult,
    SigningOptions,
    ThumbprintInvalidError,
    XMLDigitalSignatureService,
    XMLMalformedError,
    XMLSigningError,
    validate_signed_xml,
)

SigningError = XMLSigningError

_signing_service = XMLDigitalSignatureService()


def sign_xml_enveloped(
    xml_bytes: bytes,
    p12_path: str,
    password: Optional[str],
    reference_uri: str = "",
) -> bytes:
    """Sign XML with DGII-required XMLDSIG settings using a PFX/P12 certificate."""

    options = SigningOptions(
        signing_mode="pfx",
        pfx_path=p12_path,
        pfx_password=password,
        reference_uri=reference_uri,
        validate_after_sign=settings.dgii_validate_signature,
    )
    return _signing_service.sign_xml(xml_bytes, options)


def sign_xml(xml_input: bytes, signing_options: SigningOptions) -> bytes:
    """Generic XML signing entrypoint with selectable signer backend."""

    return _signing_service.sign_xml(xml_input, signing_options)


def get_certificate_metadata(signing_options: SigningOptions) -> CertificateMetadata:
    """Get certificate metadata for the configured signer backend."""

    return _signing_service.get_certificate_metadata(signing_options)


def validate_signed_xml_details(signed_xml: bytes, *, x509_cert: bytes | None = None) -> SignatureValidationResult:
    """Validate signed XML and return detailed DGII-specific diagnostics."""

    return validate_signed_xml(signed_xml, x509_cert=x509_cert)


__all__ = [
    "CanonicalizationError",
    "CertificateExpiredError",
    "CertificateMetadata",
    "CertificateNotFoundError",
    "CertificatePasswordError",
    "CertificatePrivateKeyError",
    "ExternalSignerNotConfiguredError",
    "PfxFileSigner",
    "SignatureValidationError",
    "SignatureValidationResult",
    "SigningError",
    "SigningOptions",
    "ThumbprintInvalidError",
    "XMLMalformedError",
    "XMLSigningError",
    "get_certificate_metadata",
    "sign_xml",
    "sign_xml_enveloped",
    "validate_signed_xml",
    "validate_signed_xml_details",
]
