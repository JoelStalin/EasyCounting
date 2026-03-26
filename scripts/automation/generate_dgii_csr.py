#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _build_subject(*, country: str, org: str, common_name: str, rnc: str) -> x509.Name:
    # Keep subject simple and deterministic for CA processing.
    return x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.SERIAL_NUMBER, rnc),
        ]
    )


def generate_csr_bundle(
    *,
    rnc: str,
    organization: str,
    common_name: str,
    country: str,
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    base = f"dgii_rnc_{rnc}_{stamp}"

    key_path = output_dir / f"{base}_private_key.pem"
    csr_path = output_dir / f"{base}.csr"
    readme_path = output_dir / f"{base}_README.txt"

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = _build_subject(country=country, org=organization, common_name=common_name, rnc=rnc)

    csr = x509.CertificateSigningRequestBuilder().subject_name(subject).sign(key, hashes.SHA256())

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    csr_path.write_bytes(csr.public_bytes(serialization.Encoding.PEM))

    readme = (
        "Este paquete NO es un certificado fiscal emitido.\n"
        "Contiene la solicitud (CSR) y la llave privada para solicitar el certificado real a una CA autorizada.\n\n"
        "Archivos:\n"
        f"- CSR: {csr_path}\n"
        f"- Llave privada: {key_path}\n\n"
        "Siguientes pasos:\n"
        "1. Enviar el CSR a la entidad certificadora autorizada.\n"
        "2. Recibir el certificado emitido y exportarlo a .p12/.pfx con su llave.\n"
        "3. Cargar el .p12/.pfx en el sistema DGII_ENCF (Client Portal -> Certificados o endpoint interno).\n"
    )
    readme_path.write_text(readme, encoding="utf-8")

    return {
        "key": str(key_path),
        "csr": str(csr_path),
        "readme": str(readme_path),
    }


def main() -> int:
    default_downloads = Path.home() / "Downloads"
    parser = argparse.ArgumentParser(description="Genera CSR + llave privada para solicitar certificado real DGII.")
    parser.add_argument("--rnc", required=True, help="RNC del contribuyente (solo digitos).")
    parser.add_argument("--organization", default="Contribuyente DGII", help="Razon social para el CSR.")
    parser.add_argument("--common-name", default=None, help="Common Name del CSR (default: RNC).")
    parser.add_argument("--country", default="DO", help="Pais (default: DO).")
    parser.add_argument("--output-dir", default=str(default_downloads), help="Directorio de salida.")
    args = parser.parse_args()

    rnc = "".join(ch for ch in args.rnc if ch.isdigit())
    if not rnc:
        raise SystemExit("RNC invalido")
    common_name = args.common_name or rnc

    result = generate_csr_bundle(
        rnc=rnc,
        organization=args.organization.strip() or "Contribuyente DGII",
        common_name=common_name.strip() or rnc,
        country=(args.country or "DO").strip().upper(),
        output_dir=Path(args.output_dir),
    )

    print("CSR generado:")
    print(f"- CSR: {result['csr']}")
    print(f"- Llave privada: {result['key']}")
    print(f"- README: {result['readme']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

