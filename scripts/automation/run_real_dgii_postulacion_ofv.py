#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from app.infra.settings import settings
from app.security.signing import sign_xml_enveloped


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_ROOT = PROJECT_ROOT / "tests" / "artifacts"
DEFAULT_OFV_URL = "https://dgii.gov.do/OFV/home.aspx"
DEFAULT_DEBUG_PORT = 9444
DEFAULT_API_BASE = "https://api.getupsoft.com.do"
DEFAULT_INTERNAL_API_BASE = "http://127.0.0.1:8000"
DEFAULT_SOFTWARE_NAME = "GetUpSoft DGII e-CF API"
DEFAULT_SOFTWARE_VERSION = "1.0"
DEFAULT_DGII_APP_EXE = str(
    PROJECT_ROOT / "tests" / "artifacts" / "dgii_tools" / "App_Firma_Digital" / "App Firma Digital.exe"
)
DEFAULT_CERT_STORE_PATH = "CurrentUser\\My"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_software_version(raw: str) -> str:
    candidate = (raw or "").strip()
    if re.fullmatch(r"[+-]?\d+(\.\d+)?([eE][+-]?\d+)?", candidate):
        return candidate

    parts = [part for part in candidate.split(".") if part]
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{int(parts[0])}.{int(parts[1])}"
    if parts and parts[0].isdigit():
        return str(int(parts[0]))
    return DEFAULT_SOFTWARE_VERSION


def _chrome_path() -> str:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("No se encontró Google Chrome")


def _launch_debug_chrome(port: int, run_dir: Path, start_url: str) -> None:
    chrome = _chrome_path()
    profile_dir = run_dir / "chrome-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        [
            chrome,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--new-window",
            start_url,
        ],
        cwd=PROJECT_ROOT,
    )


def _attach(port: int) -> webdriver.Chrome:
    opts = Options()
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    return webdriver.Chrome(options=opts)


def _capture(driver: webdriver.Chrome, run_dir: Path, stem: str) -> None:
    png = run_dir / f"{stem}.png"
    html = run_dir / f"{stem}.html"
    info = run_dir / f"{stem}.json"
    driver.save_screenshot(str(png))
    html.write_text(driver.page_source, encoding="utf-8")
    _write_json(
        info,
        {
            "title": driver.title,
            "url": driver.current_url,
            "body_preview": driver.find_element(By.TAG_NAME, "body").text[:6000],
        },
    )


def _wait_until(predicate, timeout: int = 60, poll: float = 1.5) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(poll)
    raise TimeoutError("Tiempo agotado esperando transición de página")


def _is_postulacion_open(driver: webdriver.Chrome) -> bool:
    current = (driver.current_url or "").lower()
    if "portalcertificacion/postulacion" in current:
        return True
    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    return "archivo de postulacion firmado" in body or "formulario de postulacion" in body
def _switch_to_window_with_url_fragment(driver: webdriver.Chrome, fragment: str) -> bool:
    target = fragment.lower()
    original = driver.current_window_handle
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if target in (driver.current_url or "").lower():
            return True
    driver.switch_to.window(original)
    return False


def _login_ofv(driver: webdriver.Chrome, username: str, password: str) -> None:
    if _is_postulacion_open(driver):
        return
    driver.get(DEFAULT_OFV_URL)
    _wait_until(lambda: bool(driver.title))

    if _is_postulacion_open(driver):
        return

    user_input = driver.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtUsuario")
    pass_input = driver.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtPassword")
    submit_btn = driver.find_elements(By.ID, "ctl00_ContentPlaceHolder1_BtnAceptar")
    if user_input and pass_input and submit_btn:
        user_input[0].clear()
        user_input[0].send_keys(username)
        pass_input[0].clear()
        pass_input[0].send_keys(password)
        submit_btn[0].click()
        _wait_until(
            lambda: "/OFV/home.aspx" in driver.current_url
            or _is_postulacion_open(driver)
            or "portalcertificacion" in driver.current_url.lower()
        )
        return

    if "/OFV/home.aspx" in driver.current_url or "portalcertificacion" in driver.current_url.lower():
        return

    raise RuntimeError("No fue posible ubicar el formulario de login OFV ni detectar una sesiÃ³n activa")


def _goto_postulacion(driver: webdriver.Chrome, run_dir: Path) -> None:
    if _is_postulacion_open(driver):
        return
    driver.get("https://dgii.gov.do/OFV/FacturaElectronica/FE_Facturador_Electronico.aspx")
    _wait_until(lambda: "Acceso Portal Facturación Electrónica" in driver.title, timeout=45)
    _capture(driver, run_dir, "postulacion_fe_access")
    access_buttons = driver.find_elements(By.ID, "ctl00_ContentPlaceHolder1_btnAcceso")
    if not access_buttons:
        _capture(driver, run_dir, "postulacion_missing_access_button")
        raise RuntimeError("No se encontro el boton de acceso al portal de certificacion en OFV")
    access_buttons[0].click()
    try:
        _wait_until(
            lambda: "portalcertificacion" in driver.current_url.lower()
            or _switch_to_window_with_url_fragment(driver, "portalcertificacion"),
            timeout=25,
        )
    except TimeoutError:
        _capture(driver, run_dir, "postulacion_portal_timeout_after_access")
        fallback_urls = [
            "https://ecf.dgii.gov.do/certecf/portalcertificacion/Postulacion/Registrado",
            "https://ecf.dgii.gov.do/CerteCF/PortalCertificacion/Postulacion/Registrado",
            "https://ecf.dgii.gov.do/certecf/portalcertificacion",
            "https://ecf.dgii.gov.do/CerteCF/PortalCertificacion",
        ]
        opened = False
        for idx, url in enumerate(fallback_urls, start=1):
            driver.get(url)
            time.sleep(6)
            _capture(driver, run_dir, f"postulacion_fallback_{idx}")
            if _is_postulacion_open(driver):
                opened = True
                break
            if "portalcertificacion" in driver.current_url.lower():
                opened = True
                break
        if not opened:
            raise RuntimeError(
                f"No fue posible abrir portal de postulacion desde OFV. URL actual={driver.current_url!r} title={driver.title!r}"
            )

    if _is_postulacion_open(driver):
        return

    view_buttons = driver.find_elements(By.ID, "btnVerPostulacionEmisor")
    if view_buttons:
        view_buttons[0].click()
        _wait_until(lambda: _is_postulacion_open(driver) or "/Postulacion/" in driver.current_url, timeout=25)
        _capture(driver, run_dir, "postulacion_after_view_button")
        return

    _capture(driver, run_dir, "postulacion_unknown_state")
    raise RuntimeError(
        f"Portal de certificacion abierto pero no se detecto formulario de postulacion ni boton esperado. "
        f"URL={driver.current_url!r} title={driver.title!r}"
    )


def _fill_form_and_generate(driver: webdriver.Chrome, run_dir: Path, api_base: str, software_name: str, software_version: str) -> Path:
    api_base = api_base.rstrip("/")
    fields = {
        "inputNombreSoftware": software_name,
        "inputVersionSoftware": software_version,
        "inputUrlRecepcion": f"{api_base}/fe/recepcion/api/ecf",
        "inputUrlAprobacionComercial": f"{api_base}/fe/aprobacioncomercial/api/ecf",
        "inputUrlAutenticacion": f"{api_base}/fe/autenticacion/api/semilla",
    }
    for element_id, value in fields.items():
        el = driver.find_element(By.ID, element_id)
        el.clear()
        el.send_keys(value)
    _capture(driver, run_dir, "filled_postulacion")

    before = {item.name for item in run_dir.iterdir()}
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(run_dir)})
    driver.find_element(By.ID, "btnGenerarArchivoValidaciones").click()
    _wait_until(lambda: any(item.name not in before and item.suffix.lower() == ".xml" for item in run_dir.iterdir()), timeout=45)
    generated = sorted(
        [item for item in run_dir.iterdir() if item.name not in before and item.suffix.lower() == ".xml"],
        key=lambda item: item.stat().st_mtime,
    )[-1]
    _capture(driver, run_dir, "generated_postulacion")
    return generated


def _sign_via_internal_api(run_dir: Path, generated_xml: Path) -> tuple[Path | None, str]:
    internal_api_base = os.getenv("DGII_INTERNAL_API_BASE_URL", DEFAULT_INTERNAL_API_BASE).strip().rstrip("/")
    internal_secret = os.getenv("DGII_INTERNAL_SERVICE_SECRET", settings.hmac_service_secret).strip()
    if not internal_api_base or not internal_secret:
        return None, "internal_api_not_configured"

    payload: dict[str, object] = {
        "xml": base64.b64encode(generated_xml.read_bytes()).decode("utf-8"),
        "allowEnvFallback": True,
    }
    tenant_id = os.getenv("DGII_POSTULACION_TENANT_ID", "").strip()
    tenant_rnc = os.getenv("DGII_POSTULACION_TENANT_RNC", "").strip()
    if tenant_id:
        try:
            payload["tenantId"] = int(tenant_id)
        except ValueError:
            return None, "invalid_tenant_id"
    if tenant_rnc:
        payload["tenantRnc"] = tenant_rnc

    body = json.dumps(payload).encode("utf-8")
    request = urlrequest.Request(
        f"{internal_api_base}/api/v1/internal/certificates/sign-xml",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Internal-Secret": internal_secret,
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urlerror.HTTPError as exc:
        error_payload = exc.read().decode("utf-8", errors="replace")
        _write_json(
            run_dir / "internal-sign-error.json",
            {
                "status": exc.code,
                "reason": exc.reason,
                "body": error_payload,
            },
        )
        return None, f"internal_api_http_{exc.code}"
    except Exception as exc:  # noqa: BLE001
        _write_json(run_dir / "internal-sign-error.json", {"error": str(exc)})
        return None, "internal_api_unreachable"

    try:
        data = json.loads(raw.decode("utf-8"))
        signed_b64 = str(data["xmlSigned"])
        signed_bytes = base64.b64decode(signed_b64)
    except Exception as exc:  # noqa: BLE001
        _write_json(
            run_dir / "internal-sign-error.json",
            {
                "error": "invalid_internal_response",
                "details": str(exc),
                "raw": raw.decode("utf-8", errors="replace"),
            },
        )
        return None, "internal_api_invalid_response"

    signed_path = run_dir / f"{generated_xml.stem}.signed.xml"
    signed_path.write_bytes(signed_bytes)
    _write_json(run_dir / "internal-sign-result.json", data)
    return signed_path, f"internal_api:{data.get('source', 'unknown')}"


def _encode_multipart_form(fields: dict[str, str], files: list[tuple[str, str, bytes, str]]) -> tuple[bytes, str]:
    boundary = f"----dgii-automation-{int(time.time() * 1000)}"
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


def _register_certificate_via_internal_api(run_dir: Path) -> str:
    p12_path_raw = os.getenv("DGII_SIGNING_P12_PATH", "").strip()
    p12_password = os.getenv("DGII_SIGNING_P12_PASSWORD", "").strip()
    if not p12_path_raw or not p12_password:
        return "register_skipped_missing_p12"

    p12_path = Path(p12_path_raw)
    if not p12_path.exists():
        return "register_skipped_missing_file"

    internal_api_base = os.getenv("DGII_INTERNAL_API_BASE_URL", DEFAULT_INTERNAL_API_BASE).strip().rstrip("/")
    internal_secret = os.getenv("DGII_INTERNAL_SERVICE_SECRET", settings.hmac_service_secret).strip()
    if not internal_api_base or not internal_secret:
        return "register_skipped_internal_api_not_configured"

    tenant_id = os.getenv("DGII_POSTULACION_TENANT_ID", "").strip()
    tenant_rnc = os.getenv("DGII_POSTULACION_TENANT_RNC", "").strip()
    alias = os.getenv("DGII_SIGNING_CERT_ALIAS", p12_path.stem).strip() or p12_path.stem

    fields = {"alias": alias, "password": p12_password, "activate": "true"}
    if tenant_id:
        fields["tenant_id"] = tenant_id
    if tenant_rnc:
        fields["tenant_rnc"] = tenant_rnc

    body, content_type = _encode_multipart_form(
        fields,
        [("certificate", p12_path.name, p12_path.read_bytes(), "application/x-pkcs12")],
    )
    request = urlrequest.Request(
        f"{internal_api_base}/api/v1/internal/certificates/register",
        data=body,
        headers={
            "Content-Type": content_type,
            "X-Internal-Secret": internal_secret,
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urlerror.HTTPError as exc:
        error_payload = exc.read().decode("utf-8", errors="replace")
        _write_json(
            run_dir / "internal-register-error.json",
            {
                "status": exc.code,
                "reason": exc.reason,
                "body": error_payload,
            },
        )
        return f"register_http_{exc.code}"
    except Exception as exc:  # noqa: BLE001
        _write_json(run_dir / "internal-register-error.json", {"error": str(exc)})
        return "register_unreachable"

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        _write_json(
            run_dir / "internal-register-error.json",
            {
                "error": "invalid_internal_register_response",
                "details": str(exc),
                "raw": raw.decode("utf-8", errors="replace"),
            },
        )
        return "register_invalid_response"

    _write_json(run_dir / "internal-register-result.json", data)
    return "register_ok"


def _sign_via_dgii_app_service(run_dir: Path, generated_xml: Path) -> tuple[Path | None, str]:
    p12_path_raw = os.getenv("DGII_SIGNING_P12_PATH", "").strip()
    p12_password = os.getenv("DGII_SIGNING_P12_PASSWORD", "").strip()
    app_exe_raw = os.getenv("DGII_APP_FIRMA_EXE_PATH", DEFAULT_DGII_APP_EXE).strip()
    if not p12_path_raw or not p12_password:
        return None, "dgii_app_missing_p12"

    p12_path = Path(p12_path_raw)
    app_exe = Path(app_exe_raw)
    if not p12_path.exists():
        return None, "dgii_app_missing_p12_file"
    if not app_exe.exists():
        return None, "dgii_app_missing_exe"

    signed_path = run_dir / f"{generated_xml.stem}.signed.xml"
    ps_script = (
        f"$exe = '{str(app_exe)}'\n"
        f"$xml = '{str(generated_xml)}'\n"
        f"$cert = '{str(p12_path)}'\n"
        f"$pass = '{p12_password}'\n"
        f"$out = '{str(signed_path)}'\n"
        "try {\n"
        "  $asm=[Reflection.Assembly]::LoadFile($exe)\n"
        "  $svcType=$asm.GetType('wfFirma.Services.SignServices')\n"
        "  if(-not $svcType){ throw 'No se encontro wfFirma.Services.SignServices' }\n"
        "  $svc=$svcType.GetProperty('Current',[Reflection.BindingFlags]'Public,Static').GetValue($null,$null)\n"
        "  $doc=$svc.FirmarXml($xml,$cert,$pass,$false)\n"
        "  $doc.Save($out)\n"
        "  Write-Output 'ok'\n"
        "  exit 0\n"
        "} catch {\n"
        "  Write-Output $_.Exception.ToString()\n"
        "  exit 1\n"
        "}\n"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0 and signed_path.exists():
        _write_json(
            run_dir / "dgii-app-sign-result.json",
            {
                "status": "ok",
                "app_exe": str(app_exe),
                "p12_path": str(p12_path),
                "stdout": proc.stdout[-4000:],
            },
        )
        return signed_path, "signed_with_dgii_app_service"

    _write_json(
        run_dir / "dgii-app-sign-error.json",
        {
            "status": "error",
            "app_exe": str(app_exe),
            "p12_path": str(p12_path),
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        },
    )
    return None, "dgii_app_failed"


def _sign_via_windows_cert_store(run_dir: Path, generated_xml: Path) -> tuple[Path | None, str]:
    thumbprint = os.getenv("DGII_SIGNING_CERT_THUMBPRINT", "").strip().replace(" ", "").upper()
    subject_contains = os.getenv("DGII_SIGNING_CERT_SUBJECT", "").strip()
    store_path = os.getenv("DGII_SIGNING_CERT_STORE_PATH", DEFAULT_CERT_STORE_PATH).strip() or DEFAULT_CERT_STORE_PATH
    if not thumbprint and not subject_contains:
        return None, "windows_store_not_configured"

    signer_script = PROJECT_ROOT / "scripts" / "automation" / "sign_with_windows_certstore.ps1"
    if not signer_script.exists():
        return None, "windows_store_signer_missing"

    signed_path = run_dir / f"{generated_xml.stem}.signed.xml"
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(signer_script),
        "-XmlPath",
        str(generated_xml),
        "-OutputPath",
        str(signed_path),
        "-StorePath",
        store_path,
    ]
    if thumbprint:
        cmd.extend(["-Thumbprint", thumbprint])
    if subject_contains:
        cmd.extend(["-SubjectContains", subject_contains])

    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if proc.returncode == 0 and signed_path.exists():
        payload: dict[str, object] = {
            "status": "ok",
            "store_path": store_path,
            "thumbprint_filter": thumbprint,
            "subject_filter": subject_contains,
            "stdout": proc.stdout[-4000:],
        }
        stdout = (proc.stdout or "").strip()
        if stdout.startswith("{") and stdout.endswith("}"):
            try:
                payload["result"] = json.loads(stdout)
            except json.JSONDecodeError:
                payload["result_parse_error"] = "stdout_was_not_valid_json"
        _write_json(run_dir / "windows-store-sign-result.json", payload)
        return signed_path, "signed_with_windows_store"

    _write_json(
        run_dir / "windows-store-sign-error.json",
        {
            "status": "error",
            "store_path": store_path,
            "thumbprint_filter": thumbprint,
            "subject_filter": subject_contains,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        },
    )
    return None, "windows_store_failed"


def _resolve_signed_xml(run_dir: Path, generated_xml: Path) -> tuple[Path | None, str]:
    signed_path_raw = os.getenv("DGII_POSTULACION_SIGNED_XML_PATH", "").strip()
    if signed_path_raw:
        signed_path = Path(signed_path_raw)
        if signed_path.exists():
            return signed_path, "provided_signed_xml"

    internal_mode = "internal_not_attempted"
    register_mode = "register_not_attempted"
    app_mode = "dgii_app_not_attempted"
    windows_store_mode = "windows_store_not_attempted"

    windows_signed_path, windows_store_mode = _sign_via_windows_cert_store(run_dir, generated_xml)
    if windows_signed_path is not None:
        return windows_signed_path, windows_store_mode

    app_signed_path, app_mode = _sign_via_dgii_app_service(run_dir, generated_xml)
    if app_signed_path is not None:
        return app_signed_path, app_mode

    internal_signed_path, internal_mode = _sign_via_internal_api(run_dir, generated_xml)
    if internal_signed_path is not None:
        return internal_signed_path, internal_mode

    register_mode = _register_certificate_via_internal_api(run_dir)
    if register_mode == "register_ok":
        internal_signed_path, internal_mode = _sign_via_internal_api(run_dir, generated_xml)
        if internal_signed_path is not None:
            return internal_signed_path, f"{internal_mode}+{register_mode}"

    p12_path_raw = os.getenv("DGII_SIGNING_P12_PATH", "").strip()
    p12_password = os.getenv("DGII_SIGNING_P12_PASSWORD", "").strip() or None
    if p12_path_raw:
        p12_path = Path(p12_path_raw)
        if p12_path.exists():
            signed_bytes = sign_xml_enveloped(generated_xml.read_bytes(), str(p12_path), p12_password)
            signed_path = run_dir / f"{generated_xml.stem}.signed.xml"
            signed_path.write_bytes(signed_bytes)
            return signed_path, f"signed_with_local_p12:{register_mode}"

    return None, f"missing_signature_material:{register_mode}:{internal_mode}:{app_mode}:{windows_store_mode}"


def _upload_signed_xml(driver: webdriver.Chrome, run_dir: Path, signed_xml: Path) -> None:
    upload = driver.find_element(By.ID, "uploadArchivoFirmado")
    upload.send_keys(str(signed_xml))
    _capture(driver, run_dir, "signed_xml_selected")
    driver.find_element(By.ID, "btnEnviarArchivoFirmado").click()
    time.sleep(8)
    _capture(driver, run_dir, "after_signed_upload")


def main() -> int:
    username = os.getenv("DGII_REAL_USERNAME", "").strip()
    password = os.getenv("DGII_REAL_PASSWORD", "").strip()
    if not username or not password:
        print("Faltan DGII_REAL_USERNAME y DGII_REAL_PASSWORD", file=sys.stderr)
        return 2

    port = int(os.getenv("DGII_DEBUG_PORT", str(DEFAULT_DEBUG_PORT)))
    api_base = os.getenv("DGII_PUBLIC_API_BASE_URL", DEFAULT_API_BASE).strip()
    software_name = os.getenv("DGII_SOFTWARE_NAME", DEFAULT_SOFTWARE_NAME).strip()
    software_version = _normalize_software_version(os.getenv("DGII_SOFTWARE_VERSION", DEFAULT_SOFTWARE_VERSION))
    run_dir = ARTIFACTS_ROOT / f"{_timestamp()}_dgii_real_postulacion_ofv"
    run_dir.mkdir(parents=True, exist_ok=True)

    _launch_debug_chrome(port, run_dir, DEFAULT_OFV_URL)
    time.sleep(8)
    driver = _attach(port)
    try:
        _capture(driver, run_dir, "ofv_login")
        _login_ofv(driver, username, password)
        _capture(driver, run_dir, "ofv_authenticated")
        _goto_postulacion(driver, run_dir)
        _capture(driver, run_dir, "postulacion_open")
        generated_xml = _fill_form_and_generate(driver, run_dir, api_base, software_name, software_version)
        signed_xml, signature_mode = _resolve_signed_xml(run_dir, generated_xml)
        summary = {
            "run_dir": str(run_dir),
            "generated_xml": str(generated_xml),
            "software_version": software_version,
            "signature_mode": signature_mode,
            "title": driver.title,
            "url": driver.current_url,
        }
        if signed_xml is not None:
            _upload_signed_xml(driver, run_dir, signed_xml)
            summary["signed_xml"] = str(signed_xml)
            summary["upload_attempted"] = True
        else:
            summary["upload_attempted"] = False
            summary["next_required"] = "Provide DGII_POSTULACION_SIGNED_XML_PATH or DGII_SIGNING_P12_PATH + DGII_SIGNING_P12_PASSWORD"
        _write_json(run_dir / "run-summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())

