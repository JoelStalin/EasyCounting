#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
from datetime import datetime
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

from app.infra.settings import settings
from app.security.signing import sign_xml_enveloped


DEFAULT_INTERNAL_API_BASE = "http://127.0.0.1:8000"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _encode_multipart_form(fields: dict[str, str], files: list[tuple[str, str, bytes, str]]) -> tuple[bytes, str]:
    boundary = f"----dgii-sign-{int(datetime.now().timestamp() * 1000)}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for field_name, filename, content, content_type in files:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                    f"Content-Type: {content_type}\r\n\r\n"
                ).encode("utf-8"),
                content,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _internal_sign(
    *,
    xml_path: Path,
    internal_api_base: str,
    internal_secret: str,
    tenant_id: int | None,
    tenant_rnc: str | None,
    allow_env_fallback: bool,
    run_dir: Path,
) -> tuple[Path | None, str]:
    payload: dict[str, object] = {
        "xml": base64.b64encode(xml_path.read_bytes()).decode("utf-8"),
        "allowEnvFallback": allow_env_fallback,
    }
    if tenant_id is not None:
        payload["tenantId"] = tenant_id
    if tenant_rnc:
        payload["tenantRnc"] = tenant_rnc

    body = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        f"{internal_api_base}/api/v1/internal/certificates/sign-xml",
        data=body,
        headers={"Content-Type": "application/json", "X-Internal-Secret": internal_secret},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8"))
        signed_bytes = base64.b64decode(str(data["xmlSigned"]))
        signed_path = run_dir / f"{xml_path.stem}.signed.xml"
        signed_path.write_bytes(signed_bytes)
        _write_json(run_dir / "internal-sign-result.json", data)
        return signed_path, f"internal_api:{data.get('source', 'unknown')}"
    except urlerror.HTTPError as exc:
        payload = {
            "status": exc.code,
            "reason": exc.reason,
            "body": exc.read().decode("utf-8", errors="replace"),
        }
        _write_json(run_dir / "internal-sign-error.json", payload)
        return None, f"internal_api_http_{exc.code}"
    except Exception as exc:  # noqa: BLE001
        _write_json(run_dir / "internal-sign-error.json", {"error": str(exc)})
        return None, "internal_api_unreachable"


def _internal_register(
    *,
    p12_path: Path,
    p12_password: str,
    alias: str,
    internal_api_base: str,
    internal_secret: str,
    tenant_id: int | None,
    tenant_rnc: str | None,
    run_dir: Path,
) -> str:
    fields = {"alias": alias, "password": p12_password, "activate": "true"}
    if tenant_id is not None:
        fields["tenant_id"] = str(tenant_id)
    if tenant_rnc:
        fields["tenant_rnc"] = tenant_rnc

    body, content_type = _encode_multipart_form(
        fields=fields,
        files=[("certificate", p12_path.name, p12_path.read_bytes(), "application/x-pkcs12")],
    )
    req = urlrequest.Request(
        f"{internal_api_base}/api/v1/internal/certificates/register",
        data=body,
        headers={"Content-Type": content_type, "X-Internal-Secret": internal_secret},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8"))
        _write_json(run_dir / "internal-register-result.json", data)
        return "register_ok"
    except urlerror.HTTPError as exc:
        payload = {
            "status": exc.code,
            "reason": exc.reason,
            "body": exc.read().decode("utf-8", errors="replace"),
        }
        _write_json(run_dir / "internal-register-error.json", payload)
        return f"register_http_{exc.code}"
    except Exception as exc:  # noqa: BLE001
        _write_json(run_dir / "internal-register-error.json", {"error": str(exc)})
        return "register_unreachable"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Firma automatica de XML de postulacion DGII con certificado del tenant o .p12 local."
    )
    parser.add_argument("--xml-path", required=True, help="Ruta del XML a firmar.")
    parser.add_argument("--output-dir", default=None, help="Directorio para evidencia y XML firmado.")
    parser.add_argument("--tenant-id", type=int, default=None, help="Tenant ID para firma interna.")
    parser.add_argument("--tenant-rnc", default=None, help="RNC del tenant para firma interna.")
    parser.add_argument("--internal-api-base", default=os.getenv("DGII_INTERNAL_API_BASE_URL", DEFAULT_INTERNAL_API_BASE))
    parser.add_argument("--internal-secret", default=os.getenv("DGII_INTERNAL_SERVICE_SECRET", settings.hmac_service_secret))
    parser.add_argument("--allow-env-fallback", action="store_true", help="Permite fallback al certificado global del backend.")
    parser.add_argument("--p12-path", default=os.getenv("DGII_SIGNING_P12_PATH", ""), help="Ruta de .p12/.pfx para registro/firma local.")
    parser.add_argument("--p12-password", default=os.getenv("DGII_SIGNING_P12_PASSWORD", ""), help="Password del .p12/.pfx.")
    parser.add_argument("--p12-alias", default=os.getenv("DGII_SIGNING_CERT_ALIAS", "Postulacion DGII"))
    args = parser.parse_args()

    xml_path = Path(args.xml_path)
    if not xml_path.exists():
        raise SystemExit(f"No existe XML: {xml_path}")
    run_dir = Path(args.output_dir) if args.output_dir else (xml_path.parent / f"{_timestamp()}_dgii_sign")
    run_dir.mkdir(parents=True, exist_ok=True)

    internal_api_base = str(args.internal_api_base).strip().rstrip("/")
    internal_secret = str(args.internal_secret).strip()
    tenant_rnc = (args.tenant_rnc or "").strip() or None
    tenant_id = args.tenant_id
    p12_path_raw = str(args.p12_path or "").strip()
    p12_password = str(args.p12_password or "").strip()

    summary: dict[str, object] = {
        "xml_path": str(xml_path),
        "run_dir": str(run_dir),
        "tenant_id": tenant_id,
        "tenant_rnc": tenant_rnc,
        "internal_api_base": internal_api_base,
    }

    signed_path, sign_mode = _internal_sign(
        xml_path=xml_path,
        internal_api_base=internal_api_base,
        internal_secret=internal_secret,
        tenant_id=tenant_id,
        tenant_rnc=tenant_rnc,
        allow_env_fallback=bool(args.allow_env_fallback),
        run_dir=run_dir,
    )
    summary["first_sign_mode"] = sign_mode
    if signed_path is not None:
        summary["signed_xml"] = str(signed_path)
        summary["status"] = "ok"
        _write_json(run_dir / "summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False))
        return 0

    register_mode = "register_skipped_missing_p12"
    p12_path = Path(p12_path_raw) if p12_path_raw else None
    if p12_path is not None and p12_path.exists() and p12_password:
        register_mode = _internal_register(
            p12_path=p12_path,
            p12_password=p12_password,
            alias=args.p12_alias.strip() or p12_path.stem,
            internal_api_base=internal_api_base,
            internal_secret=internal_secret,
            tenant_id=tenant_id,
            tenant_rnc=tenant_rnc,
            run_dir=run_dir,
        )
        summary["register_mode"] = register_mode
        if register_mode == "register_ok":
            signed_path, sign_mode = _internal_sign(
                xml_path=xml_path,
                internal_api_base=internal_api_base,
                internal_secret=internal_secret,
                tenant_id=tenant_id,
                tenant_rnc=tenant_rnc,
                allow_env_fallback=bool(args.allow_env_fallback),
                run_dir=run_dir,
            )
            summary["second_sign_mode"] = sign_mode
            if signed_path is not None:
                summary["signed_xml"] = str(signed_path)
                summary["status"] = "ok"
                _write_json(run_dir / "summary.json", summary)
                print(json.dumps(summary, ensure_ascii=False))
                return 0

    if p12_path is not None and p12_path.exists() and p12_password:
        # Last fallback: sign locally with provided .p12.
        local_signed = run_dir / f"{xml_path.stem}.signed.xml"
        signed_bytes = sign_xml_enveloped(xml_path.read_bytes(), str(p12_path), p12_password)
        local_signed.write_bytes(signed_bytes)
        summary["status"] = "ok"
        summary["local_fallback"] = True
        summary["signed_xml"] = str(local_signed)
        _write_json(run_dir / "summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False))
        return 0

    summary["status"] = "blocked"
    summary["reason"] = "No existe certificado utilizable: ni tenant activo ni .p12 local."
    _write_json(run_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

