"""DGII XMLDSIG signing services (enveloped, C14N, RSA-SHA256)."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from base64 import b64decode
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from textwrap import wrap
from typing import Literal

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
from lxml import etree
from signxml import XMLSigner, XMLVerifier, methods

from app.security.xml import XMLSecurityError, parse_secure

DGII_C14N_ALGORITHM = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
DGII_DIGEST_METHOD = "http://www.w3.org/2001/04/xmlenc#sha256"
DGII_SIGNATURE_METHOD = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
DGII_DIGEST_ALGORITHM = "sha256"
DGII_SIGNATURE_ALGORITHM = "rsa-sha256"

_XMLDSIG_NS = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_ROOT = _PROJECT_ROOT / "scripts" / "automation"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _cert_time(cert, utc_attr: str, legacy_attr: str) -> datetime:
    value = getattr(cert, utc_attr, None)
    if value is None:
        value = getattr(cert, legacy_attr)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalize_thumbprint(raw: str) -> str:
    cleaned = "".join(ch for ch in (raw or "").upper() if ch.isalnum())
    if not cleaned or any(ch not in "0123456789ABCDEF" for ch in cleaned):
        raise ThumbprintInvalidError("Thumbprint invalido: debe contener solo caracteres hexadecimales")
    if len(cleaned) != 40:
        raise ThumbprintInvalidError("Thumbprint invalido: debe tener 40 caracteres hexadecimales")
    return cleaned


def _redact_path(path: str | None) -> str:
    if not path:
        return "<empty>"
    candidate = Path(path)
    name = candidate.name or "certificado"
    return f".../{name}"


def _parse_xml_lxml(xml_input: bytes) -> etree._Element:
    try:
        parse_secure(xml_input)
    except XMLSecurityError as exc:
        raise XMLMalformedError(str(exc)) from exc
    parser = etree.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False, huge_tree=False)
    try:
        return etree.fromstring(xml_input, parser=parser)
    except etree.XMLSyntaxError as exc:
        raise XMLMalformedError(f"XML mal formado: {exc}") from exc


def _embedded_certificate_pem(signature_node: etree._Element) -> bytes | None:
    x509_node = signature_node.find(".//ds:X509Certificate", namespaces=_XMLDSIG_NS)
    if x509_node is None:
        return None
    raw_b64 = "".join((x509_node.text or "").split())
    if not raw_b64:
        return None
    try:
        b64decode(raw_b64, validate=True)
    except Exception:  # noqa: BLE001
        return None
    body = "\n".join(wrap(raw_b64, 64))
    return f"-----BEGIN CERTIFICATE-----\n{body}\n-----END CERTIFICATE-----\n".encode("ascii")


def _local_name(tag_name: str) -> str:
    return tag_name.rsplit("}", 1)[-1] if "}" in tag_name else tag_name


def _resolve_target_node(root: etree._Element, target_tag: str | None) -> etree._Element:
    if not target_tag:
        return root
    wanted = target_tag.strip()
    if not wanted:
        return root
    if _local_name(root.tag) == wanted:
        return root
    for node in root.iter():
        if _local_name(node.tag) == wanted:
            return node
    raise XMLSigningError(f"No se encontro el nodo objetivo para firmar: {wanted}")


def _ensure_output_path(output_path: str | None) -> Path | None:
    if not output_path:
        return None
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(slots=True)
class SigningOptions:
    signing_mode: Literal["pfx", "windows-store", "external"] = "pfx"
    pfx_path: str | None = None
    pfx_password: str | None = None
    thumbprint: str | None = None
    store_location: Literal["CurrentUser", "LocalMachine"] = "CurrentUser"
    store_name: str = "My"
    target_tag: str | None = None
    output_path: str | None = None
    validate_after_sign: bool = True
    reference_uri: str = ""


@dataclass(slots=True)
class CertificateMetadata:
    issuer: str
    subject: str
    thumbprint: str
    serial: str
    not_before: datetime
    not_after: datetime


@dataclass(slots=True)
class SignatureValidationResult:
    valid: bool
    has_signature: bool
    has_x509_certificate: bool
    signature_method: str | None
    digest_method: str | None
    c14n_method: str | None
    reference_uri: str | None
    errors: list[str]


class XMLSigningError(RuntimeError):
    """Base class for XML signing errors."""


class CertificateNotFoundError(XMLSigningError):
    """Raised when a certificate cannot be found."""


class CertificatePrivateKeyError(XMLSigningError):
    """Raised when the certificate has no usable private key."""


class CertificatePasswordError(XMLSigningError):
    """Raised when the PKCS#12 password is invalid."""


class CertificateExpiredError(XMLSigningError):
    """Raised when the certificate is expired or not yet valid."""


class ThumbprintInvalidError(XMLSigningError):
    """Raised when thumbprint format is invalid."""


class XMLMalformedError(XMLSigningError):
    """Raised when input XML is malformed."""


class CanonicalizationError(XMLSigningError):
    """Raised when canonicalization fails."""


class SignatureValidationError(XMLSigningError):
    """Raised when signature validation fails."""


class ExternalSignerNotConfiguredError(XMLSigningError):
    """Raised when external signer mode is requested but not configured."""


class BaseSigner:
    def sign_xml(self, xml_input: bytes, signing_options: SigningOptions) -> bytes:
        raise NotImplementedError

    def get_certificate_metadata(self, signing_options: SigningOptions) -> CertificateMetadata:
        raise NotImplementedError


class PfxFileSigner(BaseSigner):
    def _load_material(self, signing_options: SigningOptions):
        pfx_path = (signing_options.pfx_path or "").strip()
        if not pfx_path:
            raise CertificateNotFoundError("No se configuro pfxPath para firma DGII")
        path = Path(pfx_path)
        if not path.exists():
            raise CertificateNotFoundError(f"No existe el certificado PFX/P12: {_redact_path(pfx_path)}")
        try:
            bundle = path.read_bytes()
        except OSError as exc:
            raise CertificateNotFoundError(f"No se pudo leer el certificado: {_redact_path(pfx_path)}") from exc

        password = signing_options.pfx_password
        try:
            private_key, certificate, _chain = pkcs12.load_key_and_certificates(
                bundle,
                password.encode("utf-8") if password is not None else None,
            )
        except Exception as exc:  # noqa: BLE001
            raise CertificatePasswordError("Password incorrecto o PKCS#12 invalido") from exc

        if certificate is None:
            raise CertificateNotFoundError("El PKCS#12 no contiene certificado X509")
        if private_key is None:
            raise CertificatePrivateKeyError("El certificado no contiene llave privada")

        now = _utcnow()
        not_before = _cert_time(certificate, "not_valid_before_utc", "not_valid_before")
        not_after = _cert_time(certificate, "not_valid_after_utc", "not_valid_after")
        if now < not_before or now > not_after:
            raise CertificateExpiredError(
                f"Certificado fuera de vigencia (notBefore={not_before.isoformat()}, notAfter={not_after.isoformat()})"
            )
        return private_key, certificate

    def get_certificate_metadata(self, signing_options: SigningOptions) -> CertificateMetadata:
        _private_key, certificate = self._load_material(signing_options)
        return CertificateMetadata(
            issuer=certificate.issuer.rfc4514_string(),
            subject=certificate.subject.rfc4514_string(),
            thumbprint=certificate.fingerprint(hashes.SHA1()).hex().upper(),
            serial=f"{certificate.serial_number:X}",
            not_before=_cert_time(certificate, "not_valid_before_utc", "not_valid_before"),
            not_after=_cert_time(certificate, "not_valid_after_utc", "not_valid_after"),
        )

    def sign_xml(self, xml_input: bytes, signing_options: SigningOptions) -> bytes:
        private_key, certificate = self._load_material(signing_options)
        root = _parse_xml_lxml(xml_input)
        target = _resolve_target_node(root, signing_options.target_tag)

        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm=DGII_SIGNATURE_ALGORITHM,
            digest_algorithm=DGII_DIGEST_ALGORITHM,
            c14n_algorithm=DGII_C14N_ALGORITHM,
        )

        try:
            reference_uri = signing_options.reference_uri
            if reference_uri == "":
                reference_uri = None
            signed_target = signer.sign(
                target,
                key=private_key,
                cert=certificate.public_bytes(Encoding.PEM),
                reference_uri=reference_uri,
            )
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            if "c14n" in message or "canonical" in message:
                raise CanonicalizationError("Error de canonicalizacion XML (C14N)") from exc
            raise XMLSigningError("Fallo al firmar XML con PFX") from exc

        if signed_target is not root:
            parent = target.getparent()
            if parent is None:
                root = signed_target
            else:
                parent.replace(target, signed_target)
        else:
            root = signed_target

        signed_xml = etree.tostring(root, encoding="UTF-8", xml_declaration=True)
        output_path = _ensure_output_path(signing_options.output_path)
        if output_path is not None:
            output_path.write_bytes(signed_xml)

        if signing_options.validate_after_sign:
            result = validate_signed_xml(signed_xml)
            if not result.valid:
                raise SignatureValidationError(f"Firma generada pero validacion fallida: {'; '.join(result.errors)}")
        return signed_xml


class WindowsCertStoreSigner(BaseSigner):
    def _store_path(self, signing_options: SigningOptions) -> str:
        return f"{signing_options.store_location}\\{signing_options.store_name}"

    def _run_powershell(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", *args],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )

    def _require_windows(self) -> None:
        if os.name != "nt":
            raise XMLSigningError("WindowsCertStoreSigner solo esta disponible en Windows")

    def _require_thumbprint(self, signing_options: SigningOptions) -> str:
        thumbprint = (signing_options.thumbprint or "").strip()
        if not thumbprint:
            raise ThumbprintInvalidError("thumbprint es obligatorio para WindowsCertStoreSigner")
        return _normalize_thumbprint(thumbprint)

    def get_certificate_metadata(self, signing_options: SigningOptions) -> CertificateMetadata:
        self._require_windows()
        thumbprint = self._require_thumbprint(signing_options)
        list_script = _SCRIPTS_ROOT / "list_windows_signing_certificates.ps1"
        if not list_script.exists():
            raise XMLSigningError("No existe scripts/automation/list_windows_signing_certificates.ps1")

        proc = self._run_powershell(["-File", str(list_script), "-StorePath", self._store_path(signing_options)])
        if proc.returncode != 0:
            message = (proc.stderr or proc.stdout or "").strip()
            raise XMLSigningError(f"No se pudo consultar Windows Certificate Store: {message}")

        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise XMLSigningError("Respuesta invalida al consultar certificados en Windows Store") from exc

        certs = payload.get("certificates", []) if isinstance(payload, dict) else []
        selected: dict | None = None
        for cert in certs:
            if not isinstance(cert, dict):
                continue
            candidate = "".join(ch for ch in str(cert.get("thumbprint", "")).upper() if ch.isalnum())
            if candidate == thumbprint:
                selected = cert
                break
        if selected is None:
            raise CertificateNotFoundError("No se encontro certificado con el thumbprint indicado en Windows Store")

        try:
            not_before = datetime.fromisoformat(str(selected.get("not_before")))
            not_after = datetime.fromisoformat(str(selected.get("not_after")))
        except ValueError as exc:
            raise XMLSigningError("Fechas invalidas recibidas desde Windows Certificate Store") from exc

        if not_before.tzinfo is None:
            not_before = not_before.replace(tzinfo=timezone.utc)
        if not_after.tzinfo is None:
            not_after = not_after.replace(tzinfo=timezone.utc)
        now = _utcnow()
        if now < not_before or now > not_after:
            raise CertificateExpiredError(
                f"Certificado Windows fuera de vigencia (notBefore={not_before.isoformat()}, notAfter={not_after.isoformat()})"
            )

        return CertificateMetadata(
            issuer=str(selected.get("issuer", "")),
            subject=str(selected.get("subject", "")),
            thumbprint=thumbprint,
            serial="N/A",
            not_before=not_before,
            not_after=not_after,
        )

    def sign_xml(self, xml_input: bytes, signing_options: SigningOptions) -> bytes:
        self._require_windows()
        thumbprint = self._require_thumbprint(signing_options)
        sign_script = _SCRIPTS_ROOT / "sign_with_windows_certstore.ps1"
        if not sign_script.exists():
            raise XMLSigningError("No existe scripts/automation/sign_with_windows_certstore.ps1")

        with tempfile.TemporaryDirectory(prefix="dgii-win-sign-") as temp_dir:
            temp_dir_path = Path(temp_dir)
            xml_in = temp_dir_path / "unsigned.xml"
            xml_in.write_bytes(xml_input)
            xml_out = temp_dir_path / "signed.xml"

            args = [
                "-File",
                str(sign_script),
                "-XmlPath",
                str(xml_in),
                "-OutputPath",
                str(xml_out),
                "-StorePath",
                self._store_path(signing_options),
                "-Thumbprint",
                thumbprint,
            ]
            proc = self._run_powershell(args)
            if proc.returncode != 0:
                raw_error = (proc.stderr or proc.stdout or "").strip()
                lowered = raw_error.lower()
                if "no se encontro certificado" in lowered:
                    raise CertificateNotFoundError("No se encontro el certificado solicitado en Windows Store")
                if "llave privada" in lowered or "private key" in lowered:
                    raise CertificatePrivateKeyError("El certificado seleccionado no tiene llave privada usable")
                raise XMLSigningError(f"Fallo firma XML en Windows Store: {raw_error}")
            if not xml_out.exists():
                raise XMLSigningError("El script de firma reporto exito pero no genero archivo firmado")
            signed_xml = xml_out.read_bytes()

        output_path = _ensure_output_path(signing_options.output_path)
        if output_path is not None:
            output_path.write_bytes(signed_xml)

        if signing_options.validate_after_sign:
            result = validate_signed_xml(signed_xml)
            if not result.valid:
                raise SignatureValidationError(f"Firma Windows generada pero validacion fallida: {'; '.join(result.errors)}")
        return signed_xml


class ExternalSignerAdapter(BaseSigner):
    def sign_xml(self, xml_input: bytes, signing_options: SigningOptions) -> bytes:  # noqa: ARG002
        raise ExternalSignerNotConfiguredError(
            "Modo external seleccionado, pero no hay adaptador configurado para App Firma Digital/servicio externo"
        )

    def get_certificate_metadata(self, signing_options: SigningOptions) -> CertificateMetadata:  # noqa: ARG002
        raise ExternalSignerNotConfiguredError(
            "Modo external seleccionado, pero no hay adaptador configurado para App Firma Digital/servicio externo"
        )


class XMLDigitalSignatureService:
    """Reusable XMLDSIG service supporting PFX and Windows Store providers."""

    def __init__(self) -> None:
        self._pfx_signer = PfxFileSigner()
        self._windows_signer = WindowsCertStoreSigner()
        self._external_signer = ExternalSignerAdapter()

    def _resolve_signer(self, signing_options: SigningOptions) -> BaseSigner:
        mode = (signing_options.signing_mode or "pfx").strip().lower()
        if mode == "pfx":
            return self._pfx_signer
        if mode in {"windows-store", "windows_store"}:
            signing_options.signing_mode = "windows-store"
            return self._windows_signer
        if mode == "external":
            return self._external_signer
        raise XMLSigningError(f"Modo de firma no soportado: {signing_options.signing_mode}")

    def sign_xml(self, xml_input: bytes, signing_options: SigningOptions) -> bytes:
        signer = self._resolve_signer(signing_options)
        return signer.sign_xml(xml_input, signing_options)

    def get_certificate_metadata(self, signing_options: SigningOptions) -> CertificateMetadata:
        signer = self._resolve_signer(signing_options)
        return signer.get_certificate_metadata(signing_options)

    def validate_signed_xml(self, signed_xml: bytes, *, x509_cert: bytes | None = None) -> SignatureValidationResult:
        return validate_signed_xml(signed_xml, x509_cert=x509_cert)


def validate_signed_xml(signed_xml: bytes, *, x509_cert: bytes | None = None) -> SignatureValidationResult:
    has_signature = False
    has_x509_certificate = False
    signature_method: str | None = None
    digest_method: str | None = None
    c14n_method: str | None = None
    reference_uri: str | None = None
    errors: list[str] = []

    root = _parse_xml_lxml(signed_xml)
    signature_node = root.find(".//ds:Signature", namespaces=_XMLDSIG_NS)
    if signature_node is None:
        errors.append("No existe nodo Signature")
        return SignatureValidationResult(
            valid=False,
            has_signature=False,
            has_x509_certificate=False,
            signature_method=None,
            digest_method=None,
            c14n_method=None,
            reference_uri=None,
            errors=errors,
        )
    has_signature = True

    x509_node = signature_node.find(".//ds:X509Certificate", namespaces=_XMLDSIG_NS)
    has_x509_certificate = x509_node is not None and bool((x509_node.text or "").strip())
    if not has_x509_certificate:
        errors.append("La firma no incluye X509Certificate")

    signed_info = signature_node.find("./ds:SignedInfo", namespaces=_XMLDSIG_NS)
    if signed_info is None:
        errors.append("La firma no contiene SignedInfo")
    else:
        signature_method_node = signed_info.find("./ds:SignatureMethod", namespaces=_XMLDSIG_NS)
        if signature_method_node is not None:
            signature_method = signature_method_node.attrib.get("Algorithm")
        digest_method_node = signed_info.find("./ds:Reference/ds:DigestMethod", namespaces=_XMLDSIG_NS)
        if digest_method_node is not None:
            digest_method = digest_method_node.attrib.get("Algorithm")
        c14n_method_node = signed_info.find("./ds:CanonicalizationMethod", namespaces=_XMLDSIG_NS)
        if c14n_method_node is not None:
            c14n_method = c14n_method_node.attrib.get("Algorithm")
        reference_node = signed_info.find("./ds:Reference", namespaces=_XMLDSIG_NS)
        if reference_node is not None:
            reference_uri = reference_node.attrib.get("URI")

    if signature_method != DGII_SIGNATURE_METHOD:
        errors.append(f"SignatureMethod invalido: {signature_method}")
    if digest_method != DGII_DIGEST_METHOD:
        errors.append(f"DigestMethod invalido: {digest_method}")
    if c14n_method != DGII_C14N_ALGORITHM:
        errors.append(f"CanonicalizationMethod invalido: {c14n_method}")
    if reference_uri != "":
        errors.append(f"Reference URI invalido: {reference_uri!r} (se requiere URI='')")

    try:
        effective_x509 = x509_cert
        if effective_x509 is None:
            effective_x509 = _embedded_certificate_pem(signature_node)
        if x509_cert:
            XMLVerifier().verify(signed_xml, x509_cert=x509_cert)
        elif effective_x509:
            XMLVerifier().verify(signed_xml, x509_cert=effective_x509)
        else:
            XMLVerifier().verify(signed_xml)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Validacion criptografica fallida: {exc}")

    return SignatureValidationResult(
        valid=not errors,
        has_signature=has_signature,
        has_x509_certificate=has_x509_certificate,
        signature_method=signature_method,
        digest_method=digest_method,
        c14n_method=c14n_method,
        reference_uri=reference_uri,
        errors=errors,
    )
