from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from app.infra.settings import settings
from app.security.signing import get_certificate_metadata, sign_xml_enveloped, validate_signed_xml_details
from app.security.xml_dsig import SigningOptions
from app.services.browser_mcp.dgii_context import (
    add_error,
    bootstrap_summary_lines,
    can_execute,
    load_context,
    set_step_state,
)
from app.services.browser_mcp.client import BrowserMcpRemoteClient, get_browser_mcp_client
from app.services.browser_mcp.dgii_repeatability import (
    ARTIFACTS_ROOT,
    browser_policy_summary,
    classify_root_cause,
    ensure_profile_clone,
    load_auth_strategies,
    manual_seed_timeout_seconds,
    session_mode,
    summarize_console_warnings,
    write_latest_known_state,
    write_run_note,
    write_test_manifest,
)
from app.services.browser_mcp.orchestrator import run_browser_job
from app.services.browser_mcp.schemas import BrowserMcpArtifacts, BrowserMcpJobRequest, BrowserMcpJobResponse, BrowserMcpTarget


DEFAULT_API_BASE = "https://api.getupsoft.com.do"
DEFAULT_SOFTWARE_NAME = "getupsoft"
DEFAULT_SOFTWARE_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILE_ROOT = ARTIFACTS_ROOT / "_persistent_sessions" / "dgii_postulacion_browser_mcp"
_ENV_CACHE: dict[str, str] | None = None
STEP_S0 = "S0_INIT_CONTEXT"
STEP_S1 = "S1_LAUNCH_CHROME"
STEP_S2 = "S2_LOGIN_OFV"
STEP_S3 = "S3_NAVIGATE_PORTAL"
STEP_S4 = "S4_FILL_FORM"
STEP_S5 = "S5_GENERATE_XML"
STEP_S6 = "S6_SIGN_XML"
STEP_S7 = "S7_HUMAN_CONFIRM_SEND"
STEP_S8 = "S8_CAPTURE_RESPONSE"
STEP_S9 = "S9_CLOSE_SESSION"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _load_env_cache() -> dict[str, str]:
    global _ENV_CACHE
    if _ENV_CACHE is not None:
        return _ENV_CACHE
    env_path = PROJECT_ROOT / ".env"
    cache: dict[str, str] = {}
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
                value = value[1:-1]
            cache[key] = value
    _ENV_CACHE = cache
    return cache


def _env(name: str, default: str = "") -> str:
    direct = os.getenv(name)
    if direct is not None and str(direct).strip():
        return str(direct).strip()
    return _load_env_cache().get(name, default).strip()


def _normalize_software_version(raw: str) -> str:
    candidate = (raw or "").strip()
    if not candidate:
        return DEFAULT_SOFTWARE_VERSION
    parts = [part for part in candidate.split(".") if part]
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{int(parts[0])}.{int(parts[1])}"
    if parts and parts[0].isdigit():
        return str(int(parts[0]))
    return candidate


def _find_generated_xml(response_artifacts: list[str], response_result: dict[str, object]) -> Path | None:
    result_path = str(response_result.get("generatedXmlPath", "")).strip()
    if result_path:
        candidate = Path(result_path)
        if candidate.exists():
            return candidate
    xml_artifacts = [Path(item) for item in response_artifacts if item.lower().endswith(".xml")]
    if not xml_artifacts:
        return None
    xml_artifacts.sort(key=lambda item: item.stat().st_mtime)
    return xml_artifacts[-1]


def _resolve_profile_dir() -> Path:
    raw = _env("DGII_POSTULACION_PROFILE_DIR", "")
    if raw:
        path = Path(raw)
    else:
        path = DEFAULT_PROFILE_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_session_dir(run_dir: Path, mode: str) -> Path:
    if mode == "profile_clone":
        return _resolve_profile_dir()
    configured = _env("DGII_POSTULACION_SESSION_DIR", "")
    if configured:
        base = Path(configured)
        base.mkdir(parents=True, exist_ok=True)
        return base
    temporary = Path(tempfile.mkdtemp(prefix="dgii_session_", dir=str(run_dir)))
    temporary.mkdir(parents=True, exist_ok=True)
    return temporary


def _parse_bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    stripped = raw.strip()
    if not stripped:
        return default
    return stripped.lower() in {"1", "true", "yes", "on"}


def _endpoint_mode() -> str:
    mode = _env("DGII_ENDPOINT_MODE", "auto").lower()
    if mode in {"api", "fe", "auto"}:
        return mode
    return "auto"


def _portal_cred_fallback_policy() -> str:
    policy = _env("DGII_PORTAL_CRED_FALLBACK", "none").lower()
    if policy in {"none", "ofv"}:
        return policy
    return "none"


def _human_gate_enabled(env_name: str, default: bool = True) -> bool:
    return _parse_bool(_env(env_name, ""), default)


def _terminal_confirm(action: str) -> bool:
    env_key = f"DGII_CONFIRM_{action.upper()}_TERMINAL"
    raw_direct = os.getenv(env_key)
    if raw_direct is not None:
        return raw_direct.strip().upper() in {"YES", "Y", "CONFIRM"}
    value = _env(env_key, "").upper()
    if value in {"YES", "Y", "CONFIRM"}:
        return True
    if not sys.stdin.isatty():
        return False
    try:
        entered = input(f"[DGII] Confirmar {action} (type YES): ").strip().upper()
    except EOFError:
        return False
    return entered == "YES"


def _mcp_confirm(action: str) -> bool:
    env_key = f"DGII_CONFIRM_{action.upper()}_MCP"
    return _parse_bool(_env(env_key, ""), default=False)


def _require_dual_confirmation(action: str) -> tuple[bool, dict[str, object]]:
    mcp_ok = _mcp_confirm(action)
    terminal_ok = _terminal_confirm(action)
    return mcp_ok and terminal_ok, {"mcp": mcp_ok, "terminal": terminal_ok}


def _keep_browser_open_on_failure(headless: bool) -> bool:
    if headless:
        return False
    raw = _env("DGII_POSTULACION_KEEP_BROWSER_OPEN_ON_FAILURE", "").lower()
    if raw:
        return raw in {"1", "true", "yes", "on"}
    return True


def _build_metadata(
    *,
    username: str,
    password: str,
    api_base: str,
    software_name: str,
    software_version: str,
    signed_xml_path: str | None = None,
    endpoint_contract: str | None = None,
) -> dict[str, object]:
    portal_fallback = _portal_cred_fallback_policy()
    portal_username = _env("DGII_CERT_PORTAL_USERNAME", "")
    portal_password = _env("DGII_CERT_PORTAL_PASSWORD", "")
    if portal_fallback == "ofv":
        portal_username = portal_username or username
        portal_password = portal_password or password
    metadata: dict[str, object] = {
        "username": username,
        "password": password,
        "portalUsername": portal_username,
        "portalPassword": portal_password,
        "portalCredentialFallback": portal_fallback,
        "apiBase": api_base.rstrip("/"),
        "softwareName": software_name,
        "softwareVersion": software_version,
        "endpointMode": endpoint_contract or _endpoint_mode(),
        "sessionMode": session_mode(),
        "authStrategies": load_auth_strategies(),
        "manualSeedTimeoutSeconds": manual_seed_timeout_seconds(),
        "policyBaseline": _env("DGII_POSTULACION_POLICY_BASELINE", "") or "strict_normal_browser",
    }
    pause_before_generate_seconds = _env("DGII_POSTULACION_PAUSE_BEFORE_GENERATE_SECONDS", "")
    if pause_before_generate_seconds:
        metadata["pauseBeforeGenerateSeconds"] = pause_before_generate_seconds
    if signed_xml_path:
        metadata["signedXmlPath"] = signed_xml_path
    return metadata


def _load_signing_order() -> list[str]:
    raw = _env(
        "DGII_POSTULACION_SIGNING_ORDER",
        "internal_api,internal_api_after_register,local_p12,windows_store,dgii_app",
    )
    allowed = {
        "provided_signed_xml",
        "internal_api",
        "internal_api_after_register",
        "local_p12",
        "windows_store",
        "dgii_app",
    }
    ordered = [item.strip().lower() for item in raw.split(",") if item.strip()]
    normalized = [item for item in ordered if item in allowed]
    return normalized or ["internal_api", "internal_api_after_register", "local_p12", "windows_store", "dgii_app"]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _certificate_metadata_for_p12(p12_path: Path, p12_password: str | None) -> dict[str, object]:
    metadata = get_certificate_metadata(
        SigningOptions(signing_mode="pfx", pfx_path=str(p12_path), pfx_password=p12_password)
    )
    return {
        "issuer": metadata.issuer,
        "subject": metadata.subject,
        "thumbprint": metadata.thumbprint,
        "serial": metadata.serial,
        "notBefore": metadata.not_before.isoformat(),
        "notAfter": metadata.not_after.isoformat(),
    }


def _signature_diagnostics(signed_xml_path: Path) -> dict[str, object]:
    validation = validate_signed_xml_details(signed_xml_path.read_bytes())
    return {
        "valid": validation.valid,
        "hasSignature": validation.has_signature,
        "hasX509Certificate": validation.has_x509_certificate,
        "signatureMethod": validation.signature_method,
        "digestMethod": validation.digest_method,
        "c14nMethod": validation.c14n_method,
        "referenceUri": validation.reference_uri,
        "errors": validation.errors,
    }


def _postulacion_identity_diagnostics(generated_xml: Path, p12_path: Path, p12_password: str | None) -> dict[str, object]:
    certificate = _certificate_metadata_for_p12(p12_path, p12_password)
    root = ET.fromstring(generated_xml.read_bytes())
    representative_rnc = (root.findtext("./Representante/RNCRepresentante") or "").strip()
    representative_name = (root.findtext("./Representante/NombreRepresentante") or "").strip()
    subject = str(certificate.get("subject", ""))
    warnings: list[str] = []
    if representative_rnc and representative_rnc not in subject:
        warnings.append("certificate_subject_missing_representative_rnc")
    normalized_name = " ".join(representative_name.upper().split())
    if normalized_name and normalized_name not in subject.upper():
        warnings.append("certificate_subject_missing_representative_name")
    return {
        "representativeRnc": representative_rnc,
        "representativeName": representative_name,
        "certificate": certificate,
        "warnings": warnings,
    }


def _resolve_p12_source(run_dir: Path) -> tuple[Path | None, str | None, str | None]:
    request_code = _env("DGII_VIAFIRMA_REQUEST_CODE", "")
    if request_code:
        from scripts.automation.viafirma_download import redownload_viafirma_certificate

        downloaded = redownload_viafirma_certificate(request_code, output_dir=run_dir / "viafirma")
        password = _env("DGII_SIGNING_P12_PASSWORD", "") or settings.dgii_effective_pfx_password or None
        return downloaded, password, f"viafirma:{request_code}"

    p12_path_raw = _env("DGII_SIGNING_P12_PATH", "") or settings.dgii_effective_pfx_path
    if not p12_path_raw:
        return None, None, "missing"
    password = _env("DGII_SIGNING_P12_PASSWORD", "") or settings.dgii_effective_pfx_password or None
    return Path(p12_path_raw), password, "configured"


def _record_signature_attempt(
    attempts: list[dict[str, object]],
    *,
    method: str,
    mode: str,
    signed_xml_path: Path | None,
    error: str | None = None,
    p12_path: Path | None = None,
    p12_password: str | None = None,
) -> None:
    payload: dict[str, object] = {
        "method": method,
        "mode": mode,
        "signedXmlPath": str(signed_xml_path) if signed_xml_path else None,
        "error": error,
    }
    if p12_path is not None and p12_path.exists():
        try:
            payload["certificate"] = _certificate_metadata_for_p12(p12_path, p12_password)
        except Exception as exc:  # noqa: BLE001
            payload["certificateError"] = str(exc)
    if signed_xml_path is not None and signed_xml_path.exists():
        try:
            payload["validation"] = _signature_diagnostics(signed_xml_path)
        except Exception as exc:  # noqa: BLE001
            payload["validationError"] = str(exc)
    attempts.append(payload)


def _resolve_signed_xml_optimized(run_dir: Path, generated_xml: Path) -> tuple[Path | None, str]:
    from scripts.automation.run_real_dgii_postulacion_ofv import (
        _register_certificate_via_internal_api,
        _sign_via_dgii_app_service,
        _sign_via_internal_api,
        _sign_via_windows_cert_store,
    )

    attempts: list[dict[str, object]] = []
    order = _load_signing_order()
    p12_path, p12_password, p12_source = _resolve_p12_source(run_dir)
    internal_mode = "internal_not_attempted"
    register_mode = "register_not_attempted"
    windows_store_mode = "windows_store_not_attempted"
    app_mode = "dgii_app_not_attempted"

    for method in order:
        if method == "provided_signed_xml":
            signed_path_raw = _env("DGII_POSTULACION_SIGNED_XML_PATH", "")
            if signed_path_raw:
                signed_path = Path(signed_path_raw)
                if signed_path.exists():
                    _record_signature_attempt(attempts, method=method, mode="provided_signed_xml", signed_xml_path=signed_path)
                    _write_json(run_dir / "signature-attempts.json", {"order": order, "attempts": attempts})
                    return signed_path, "provided_signed_xml"
            _record_signature_attempt(attempts, method=method, mode="provided_signed_xml", signed_xml_path=None, error="missing_file")
            continue

        if method == "internal_api":
            internal_signed_path, internal_mode = _sign_via_internal_api(run_dir, generated_xml)
            _record_signature_attempt(
                attempts,
                method=method,
                mode=internal_mode,
                signed_xml_path=internal_signed_path,
                error=None if internal_signed_path else internal_mode,
            )
            if internal_signed_path is not None:
                _write_json(run_dir / "signature-attempts.json", {"order": order, "attempts": attempts})
                return internal_signed_path, f"preferred:{internal_mode}"
            continue

        if method == "internal_api_after_register":
            register_mode = _register_certificate_via_internal_api(run_dir)
            if register_mode == "register_ok":
                internal_signed_path, internal_mode = _sign_via_internal_api(run_dir, generated_xml)
            else:
                internal_signed_path = None
            _record_signature_attempt(
                attempts,
                method=method,
                mode=f"{register_mode}:{internal_mode}",
                signed_xml_path=internal_signed_path,
                error=None if internal_signed_path else f"{register_mode}:{internal_mode}",
            )
            if internal_signed_path is not None:
                _write_json(run_dir / "signature-attempts.json", {"order": order, "attempts": attempts})
                return internal_signed_path, f"preferred:{internal_mode}+{register_mode}"
            continue

        if method == "local_p12":
            if p12_path and p12_path.exists():
                try:
                    signed_bytes = sign_xml_enveloped(generated_xml.read_bytes(), str(p12_path), p12_password)
                    signed_path = run_dir / f"{generated_xml.stem}.signed.xml"
                    signed_path.write_bytes(signed_bytes)
                    _record_signature_attempt(
                        attempts,
                        method=method,
                        mode=f"local_p12:{p12_source}:{register_mode}:{internal_mode}",
                        signed_xml_path=signed_path,
                        p12_path=p12_path,
                        p12_password=p12_password,
                    )
                    _write_json(run_dir / "signature-attempts.json", {"order": order, "attempts": attempts})
                    return signed_path, f"preferred:local_p12:{p12_source}:{register_mode}:{internal_mode}"
                except Exception as exc:  # noqa: BLE001
                    _record_signature_attempt(
                        attempts,
                        method=method,
                        mode="local_p12_failed",
                        signed_xml_path=None,
                        error=str(exc),
                        p12_path=p12_path,
                        p12_password=p12_password,
                    )
                    continue
            _record_signature_attempt(attempts, method=method, mode="local_p12_missing", signed_xml_path=None, error="missing_p12")
            continue

        if method == "windows_store":
            windows_signed_path, windows_store_mode = _sign_via_windows_cert_store(run_dir, generated_xml)
            _record_signature_attempt(
                attempts,
                method=method,
                mode=windows_store_mode,
                signed_xml_path=windows_signed_path,
                error=None if windows_signed_path else windows_store_mode,
            )
            if windows_signed_path is not None:
                _write_json(run_dir / "signature-attempts.json", {"order": order, "attempts": attempts})
                return windows_signed_path, f"fallback:{windows_store_mode}"
            continue

        if method == "dgii_app":
            app_signed_path, app_mode = _sign_via_dgii_app_service(run_dir, generated_xml)
            _record_signature_attempt(
                attempts,
                method=method,
                mode=app_mode,
                signed_xml_path=app_signed_path,
                error=None if app_signed_path else app_mode,
                p12_path=p12_path if p12_path and p12_path.exists() else None,
                p12_password=p12_password,
            )
            if app_signed_path is not None:
                _write_json(run_dir / "signature-attempts.json", {"order": order, "attempts": attempts})
                return app_signed_path, f"fallback:{app_mode}"
            continue

    _write_json(run_dir / "signature-attempts.json", {"order": order, "attempts": attempts})
    return None, f"missing_signature_material:{register_mode}:{internal_mode}:{windows_store_mode}:{app_mode}"


def _extract_portal_auth_result(response: BrowserMcpJobResponse | None) -> str:
    if response is None:
        return "not_attempted"
    result = response.result if isinstance(response.result, dict) else {}
    for key in ("portalAuthResult", "responseClassification"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            classification = value.get("classification")
            if isinstance(classification, str) and classification.strip():
                return classification.strip()
    ranked_values: list[str] = []
    for step in response.step_results:
        details = step.get("details") or {}
        if not isinstance(details, dict):
            continue
        value = details.get("portalAuthResult")
        if isinstance(value, str) and value.strip():
            ranked_values.append(value.strip())
    if not ranked_values:
        return "unknown"
    priorities = [
        "invalid_credentials",
        "authenticated",
        "manual_seed_timeout",
        "login_required",
        "unknown",
    ]
    lowered = [item.lower() for item in ranked_values]
    for candidate in priorities:
        if candidate in lowered:
            return candidate
    return ranked_values[-1]


def _extract_auth_strategy_attempted(response: BrowserMcpJobResponse | None) -> str:
    if response is None:
        return "not_attempted"
    preferred_names = {
        "ofv_session_reuse",
        "portal_state_probe",
        "portal_credentials_attempt",
        "manual_seed_hold",
        "session_reuse",
        "portal_credentials",
        "manual_seed",
    }
    seen: list[str] = []
    for step in response.step_results:
        name = str(step.get("name", "")).strip()
        if name in preferred_names and name not in seen:
            seen.append(name)
    return ",".join(seen) if seen else "unknown"


def _combine_artifacts(*responses: BrowserMcpJobResponse | None) -> list[str]:
    combined: list[str] = []
    for response in responses:
        if response is None:
            continue
        for artifact in response.artifacts:
            if artifact not in combined:
                combined.append(artifact)
    return combined


def _runtime_metadata(response: BrowserMcpJobResponse | None) -> dict[str, object]:
    if response is None:
        return {
            "runtime_job_id": None,
            "runtime_retained": False,
            "current_url": None,
        }
    result = response.result if isinstance(response.result, dict) else {}
    return {
        "runtime_job_id": response.job_id,
        "runtime_retained": bool(result.get("browserRetained")),
        "current_url": response.final_url,
    }


def _resume_action(summary: dict[str, object]) -> str:
    if summary.get("runtime_retained"):
        return "resume_from_retained_runtime"
    if summary.get("profile_dir"):
        return "resume_from_persistent_profile"
    return "restart_from_clean_session"


def _write_session_log(run_dir: Path, payload: dict[str, object]) -> Path:
    path = run_dir / "session_log.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _copy_if_present(source: Path, destination: Path) -> Path | None:
    if not source.exists():
        return None
    if source.resolve() == destination.resolve():
        return source
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _latest_artifact(artifacts: list[str], suffixes: set[str]) -> Path | None:
    candidates: list[Path] = []
    for artifact in artifacts:
        path = Path(artifact)
        if not path.exists():
            continue
        if path.suffix.lower() not in suffixes:
            continue
        candidates.append(path)
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.stat().st_mtime)
    return candidates[-1]


def _copy_latest_artifact(artifacts: list[str], suffixes: set[str], destination: Path) -> Path | None:
    source = _latest_artifact(artifacts, suffixes)
    if source is None:
        return None
    return _copy_if_present(source, destination)


def _apply_runtime_metadata(summary: dict[str, object], response: BrowserMcpJobResponse | None) -> None:
    metadata = _runtime_metadata(response)
    summary.update(metadata)
    summary["chrome_runtime_id"] = metadata["runtime_job_id"]
    summary["browser_kept_open"] = metadata["runtime_retained"]


def _persist_outputs(
    *,
    run_dir: Path,
    summary: dict[str, object],
    ctx: dict[str, object],
    session_started_at: datetime,
    session_dir: Path,
    mode: str,
) -> dict[str, object]:
    finished_at = datetime.now()
    duration_minutes = round(max(0.0, (finished_at - session_started_at).total_seconds()) / 60.0, 2)
    operator_id = _env("DGII_OPERATOR_ID", "")

    summary.setdefault("session_mode", mode)
    summary["session_started_at"] = session_started_at.isoformat()
    summary["session_finished_at"] = finished_at.isoformat()
    summary["session_duration_minutes"] = duration_minutes
    summary["session_dir"] = str(session_dir)
    if operator_id:
        summary["operator_id"] = operator_id
    if summary.get("runtime_job_id") and not summary.get("chrome_runtime_id"):
        summary["chrome_runtime_id"] = summary.get("runtime_job_id")

    run_summary_path = run_dir / "run-summary.json"
    run_summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    session_payload = {
        "session_id": ctx.get("session_id"),
        "session_mode": summary.get("session_mode"),
        "session_started_at": summary.get("session_started_at"),
        "session_finished_at": summary.get("session_finished_at"),
        "session_duration_minutes": summary.get("session_duration_minutes"),
        "operator_id": summary.get("operator_id"),
        "state_map": ctx.get("state_map", {}),
        "active_errors": [item for item in (ctx.get("state_map", {}) or {}).get("active_errors", []) if item],
        "runtime_job_id": summary.get("runtime_job_id"),
        "runtime_retained": summary.get("runtime_retained"),
        "current_url": summary.get("current_url"),
        "profile_dir": summary.get("profile_dir"),
        "auth_strategy_attempted": summary.get("auth_strategy_attempted"),
        "portal_auth_result": summary.get("portal_auth_result"),
        "endpoint_contract_selected": summary.get("endpoint_contract_selected"),
        "portal_auth_policy": summary.get("portal_auth_policy"),
        "resume_action": summary.get("resume_action"),
        "root_cause": summary.get("root_cause"),
        "upload_attempted": summary.get("upload_attempted"),
    }
    session_log_path = _write_session_log(run_dir, session_payload)
    summary["session_log"] = str(session_log_path)
    summary["run_summary_path"] = str(run_summary_path)

    write_latest_known_state(summary)
    note_path = write_run_note(summary)
    summary["run_note_path"] = str(note_path)
    run_summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _release_retained_runtime(job_id: str) -> bool:
    client = get_browser_mcp_client()
    if not isinstance(client, BrowserMcpRemoteClient):
        return False
    return client.release_runtime(job_id)


def _detect_signing_methods() -> list[str]:
    methods: list[str] = []
    if _env("DGII_SIGNING_CERT_THUMBPRINT", "") and _env("DGII_SIGNING_CERT_SUBJECT", ""):
        methods.append("A_WINDOWS_STORE")
    if _env("DGII_SIGNING_P12_PATH", "") and _env("DGII_SIGNING_P12_PASSWORD", ""):
        methods.append("B_P12_OR_APP")
    if (
        _env("DGII_INTERNAL_API_BASE_URL", "")
        and _env("DGII_INTERNAL_SERVICE_SECRET", "")
        and _env("DGII_POSTULACION_TENANT_ID", "")
    ):
        methods.append("C_INTERNAL_API")
    return methods


def _validate_preflight_env(ctx: dict[str, object]) -> dict[str, object]:
    required = [
        "DGII_REAL_USERNAME",
        "DGII_REAL_PASSWORD",
        "DGII_PUBLIC_API_BASE_URL",
        "DGII_SOFTWARE_NAME",
        "DGII_SOFTWARE_VERSION",
    ]
    missing = [name for name in required if not _env(name, "")]
    if missing:
        raise RuntimeError(f"Variables obligatorias faltantes: {missing}")
    methods = _detect_signing_methods()
    has_signed_path = bool(_env("DGII_POSTULACION_SIGNED_XML_PATH", ""))
    if not methods and not has_signed_path:
        raise RuntimeError("Ningun metodo de firma completo detectado y no existe DGII_POSTULACION_SIGNED_XML_PATH")
    if len(methods) > 1:
        raise RuntimeError(f"Mas de un metodo de firma completo detectado: {methods}. Debe quedar uno solo.")
    ctx["env_vars_present"] = sorted([key for key in os.environ if key.startswith("DGII_")])
    ctx["signing_method_detected"] = methods[0] if methods else "PROVIDED_SIGNED_XML"
    return {"missing": missing, "signing_method_detected": ctx["signing_method_detected"]}


def run_postulacion_emisor_flow() -> dict[str, object]:
    ctx = load_context()
    for line in bootstrap_summary_lines(ctx):
        print(line)

    set_step_state(ctx, STEP_S0, "RUNNING", "Inicializando contexto y validando entorno")
    try:
        _validate_preflight_env(ctx)
    except Exception as exc:  # noqa: BLE001
        add_error(ctx, step_id=STEP_S0, code="ENV_CHECK_FAILED", description=str(exc))
        raise
    set_step_state(ctx, STEP_S0, "DONE", "Contexto y preflight completados")

    ok, reason = can_execute(STEP_S1, ctx)
    if not ok:
        raise RuntimeError(reason)
    set_step_state(ctx, STEP_S1, "RUNNING", "Preparando sesion Browser MCP")

    username = _env("DGII_REAL_USERNAME", "")
    password = _env("DGII_REAL_PASSWORD", "")
    api_base = _env("DGII_PUBLIC_API_BASE_URL", DEFAULT_API_BASE) or DEFAULT_API_BASE
    software_name = _env("DGII_SOFTWARE_NAME", DEFAULT_SOFTWARE_NAME) or DEFAULT_SOFTWARE_NAME
    software_version = _normalize_software_version(_env("DGII_SOFTWARE_VERSION", DEFAULT_SOFTWARE_VERSION))
    mode = session_mode()
    endpoint_mode = _endpoint_mode()
    headless_env = _env("DGII_PORTAL_HEADLESS", "")
    headless = _parse_bool(headless_env, default=(False if mode == "direct" else True))
    keep_browser_open_on_failure = _keep_browser_open_on_failure(headless)
    keep_session_open = _parse_bool(_env("DGII_KEEP_SESSION_OPEN", ""), True)
    run_dir = ARTIFACTS_ROOT / f"{_timestamp()}_dgii_direct_session"
    run_dir.mkdir(parents=True, exist_ok=True)
    session_started_at = datetime.now()
    write_test_manifest()

    if mode == "profile_clone":
        profile_bootstrap = ensure_profile_clone()
        session_dir = Path(str(profile_bootstrap["profileDir"]))
    else:
        session_dir = _resolve_session_dir(run_dir, mode)
        profile_bootstrap = {
            "profileDir": str(session_dir),
            "sourceProfile": "direct_session",
            "bootstrapped": True,
            "bootstrapManifestPath": None,
        }
    set_step_state(ctx, STEP_S1, "DONE", f"Sesion preparada en {session_dir}")

    generated_response: BrowserMcpJobResponse | None = None
    upload_response: BrowserMcpJobResponse | None = None
    selected_contract = endpoint_mode
    contracts_to_try = [endpoint_mode] if endpoint_mode in {"api", "fe"} else ["api", "fe"]

    ok, reason = can_execute(STEP_S2, ctx)
    if not ok:
        raise RuntimeError(reason)
    set_step_state(ctx, STEP_S2, "RUNNING", "Autenticando OFV y navegando a portal")
    for contract in contracts_to_try:
        selected_contract = contract
        common_target = BrowserMcpTarget(
            metadata=_build_metadata(
                username=username,
                password=password,
                api_base=api_base,
                software_name=software_name,
                software_version=software_version,
                endpoint_contract=contract,
            )
        )
        generated_response = run_browser_job(
            BrowserMcpJobRequest(
                scenario="dgii-postulacion-generate-xml",
                mode="persistent_profile",
                userDataDir=str(session_dir),
                headless=headless,
                keepOpenOnFailure=keep_browser_open_on_failure,
                keepOpenOnSuccess=False,
                target=common_target,
                artifacts=BrowserMcpArtifacts(screenshot=True, snapshot=True, pdf=False, trace=True, saveSession=True),
                outputDir=str(run_dir),
            )
        )
        if generated_response.status == "completed":
            break

    if generated_response is None:
        raise RuntimeError("No se ejecuto el escenario de generacion")

    warning_summary = summarize_console_warnings(generated_response.artifacts)
    if generated_response.status != "completed":
        set_step_state(ctx, STEP_S2, "ERROR", "Fallo en autenticacion/navegacion")
        add_error(
            ctx,
            step_id=STEP_S2,
            code="GENERATE_XML_FAILED",
            description=str(generated_response.error or "run_browser_job failed"),
        )
        runtime_metadata = _runtime_metadata(generated_response)
        summary = {
            "run_dir": str(run_dir),
            "session_mode": mode,
            "stage": "generate_xml",
            "status": generated_response.status,
            "error": generated_response.error,
            "artifacts": generated_response.artifacts,
            "profile_dir": str(session_dir),
            "profile_source": profile_bootstrap["sourceProfile"],
            "profile_bootstrap": profile_bootstrap,
            "policy_baseline": browser_policy_summary(),
            "warning_summary": warning_summary,
            "auth_strategy_attempted": _extract_auth_strategy_attempted(generated_response),
            "portal_auth_result": _extract_portal_auth_result(generated_response),
            "endpoint_contract_selected": selected_contract,
            "portal_auth_policy": _portal_cred_fallback_policy(),
            **runtime_metadata,
            "chrome_runtime_id": runtime_metadata["runtime_job_id"],
            "browser_kept_open": runtime_metadata["runtime_retained"],
            "resume_action": _resume_action(
                {
                    "runtime_retained": runtime_metadata["runtime_retained"],
                    "profile_dir": str(session_dir),
                }
            ),
            "resume_hint": "Sesion persistida en profile_dir para reintento.",
        }
        summary["root_cause"] = classify_root_cause(summary)
        return _persist_outputs(
            run_dir=run_dir,
            summary=summary,
            ctx=ctx,
            session_started_at=session_started_at,
            session_dir=session_dir,
            mode=mode,
        )

    set_step_state(ctx, STEP_S2, "DONE", "Login OFV completado")
    ok, reason = can_execute(STEP_S3, ctx)
    if not ok:
        raise RuntimeError(reason)
    set_step_state(ctx, STEP_S3, "RUNNING", "Navegando al portal de certificacion")
    set_step_state(ctx, STEP_S3, "DONE", "Portal de certificacion abierto")

    ok, reason = can_execute(STEP_S4, ctx)
    if not ok:
        raise RuntimeError(reason)
    set_step_state(ctx, STEP_S4, "RUNNING", "Completando formulario de postulacion")
    set_step_state(ctx, STEP_S4, "DONE", "Formulario completado")

    ok, reason = can_execute(STEP_S5, ctx)
    if not ok:
        raise RuntimeError(reason)
    set_step_state(ctx, STEP_S5, "RUNNING", "Generando XML de postulacion")
    generated_xml = _find_generated_xml(generated_response.artifacts, generated_response.result)
    if generated_xml is None or not generated_xml.exists():
        add_error(ctx, step_id=STEP_S5, code="XML_NOT_FOUND", description="No fue posible localizar el XML generado")
        raise RuntimeError("No fue posible localizar el XML generado por la postulacion")
    generated_xml_canonical = _copy_if_present(generated_xml, run_dir / "postulacion_generado.xml")
    set_step_state(ctx, STEP_S5, "DONE", "XML generado")

    ok, reason = can_execute(STEP_S6, ctx)
    if not ok:
        raise RuntimeError(reason)
    if _human_gate_enabled("DGII_REQUIRE_CONFIRM_SIGN", True):
        set_step_state(ctx, STEP_S6, "WAITING_HUMAN", "Esperando confirmacion humana para firmar")
        sign_confirmed, sign_channels = _require_dual_confirmation("SIGN")
        if not sign_confirmed:
            summary = {
                "run_dir": str(run_dir),
                "session_mode": mode,
                "status": "waiting_human",
                "generated_xml": str(generated_xml),
                "postulacion_generado_xml": str(generated_xml_canonical) if generated_xml_canonical else str(generated_xml),
                "profile_dir": str(session_dir),
                "portal_auth_policy": _portal_cred_fallback_policy(),
                "endpoint_contract_selected": selected_contract,
                "confirmations": {"sign": sign_channels},
                "upload_attempted": False,
                "next_required": "Confirm sign action via MCP and terminal",
            }
            _apply_runtime_metadata(summary, generated_response)
            summary["resume_action"] = _resume_action(summary)
            summary["root_cause"] = "waiting_human_confirmation_sign"
            return _persist_outputs(
                run_dir=run_dir,
                summary=summary,
                ctx=ctx,
                session_started_at=session_started_at,
                session_dir=session_dir,
                mode=mode,
            )
    set_step_state(ctx, STEP_S6, "RUNNING", "Firmando XML")

    signed_xml, signature_mode = _resolve_signed_xml_optimized(run_dir, generated_xml)
    summary: dict[str, object] = {
        "run_dir": str(run_dir),
        "session_mode": mode,
        "profile_dir": str(session_dir),
        "profile_source": profile_bootstrap["sourceProfile"],
        "profile_bootstrap": profile_bootstrap,
        "policy_baseline": browser_policy_summary(),
        "generated_xml": str(generated_xml),
        "postulacion_generado_xml": str(generated_xml_canonical) if generated_xml_canonical else str(generated_xml),
        "generate_job": {
            "status": generated_response.status,
            "artifacts": generated_response.artifacts,
            "result": generated_response.result,
            "step_results": generated_response.step_results,
        },
        "software_version": software_version,
        "signature_mode": signature_mode,
        "keep_browser_open_on_failure": keep_browser_open_on_failure,
        "auth_strategy_attempted": _extract_auth_strategy_attempted(generated_response),
        "portal_auth_result": _extract_portal_auth_result(generated_response),
        "endpoint_contract_selected": selected_contract,
        "portal_auth_policy": _portal_cred_fallback_policy(),
    }
    p12_path, p12_password, p12_source = _resolve_p12_source(run_dir)
    summary["p12_source"] = p12_source
    if p12_path and p12_path.exists():
        try:
            summary["identity_diagnostics"] = _postulacion_identity_diagnostics(generated_xml, p12_path, p12_password)
        except Exception as exc:  # noqa: BLE001
            summary["identity_diagnostics_error"] = str(exc)

    if signed_xml is None:
        set_step_state(ctx, STEP_S6, "ERROR", "No se pudo firmar XML")
        add_error(
            ctx,
            step_id=STEP_S6,
            code="SIGNING_FAILED",
            description="No se pudo obtener XML firmado",
        )
        summary["upload_attempted"] = False
        summary["next_required"] = (
            "Provide DGII_POSTULACION_SIGNED_XML_PATH or DGII_SIGNING_P12_PATH + DGII_SIGNING_P12_PASSWORD"
        )
        _apply_runtime_metadata(summary, generated_response)
        summary["warning_summary"] = summarize_console_warnings(_combine_artifacts(generated_response))
        summary["resume_action"] = _resume_action(summary)
        summary["root_cause"] = classify_root_cause(summary)
        return _persist_outputs(
            run_dir=run_dir,
            summary=summary,
            ctx=ctx,
            session_started_at=session_started_at,
            session_dir=session_dir,
            mode=mode,
        )
    set_step_state(ctx, STEP_S6, "DONE", f"XML firmado con {signature_mode}")
    signed_xml_canonical = _copy_if_present(signed_xml, run_dir / "postulacion_firmado.xml")

    ok, reason = can_execute(STEP_S7, ctx)
    if not ok:
        raise RuntimeError(reason)
    if _human_gate_enabled("DGII_REQUIRE_CONFIRM_UPLOAD", True):
        set_step_state(ctx, STEP_S7, "WAITING_HUMAN", "Esperando confirmacion humana para envio")
        upload_confirmed, upload_channels = _require_dual_confirmation("UPLOAD")
        if not upload_confirmed:
            summary["signed_xml"] = str(signed_xml)
            summary["postulacion_firmado_xml"] = str(signed_xml_canonical) if signed_xml_canonical else str(signed_xml)
            summary["upload_attempted"] = False
            summary["confirmations"] = {"upload": upload_channels}
            summary["next_required"] = "Confirm upload action via MCP and terminal"
            _apply_runtime_metadata(summary, generated_response)
            summary["resume_action"] = _resume_action(summary)
            summary["root_cause"] = "waiting_human_confirmation_upload"
            return _persist_outputs(
                run_dir=run_dir,
                summary=summary,
                ctx=ctx,
                session_started_at=session_started_at,
                session_dir=session_dir,
                mode=mode,
            )
    set_step_state(ctx, STEP_S7, "RUNNING", "Subiendo XML firmado")

    upload_target = BrowserMcpTarget(
        metadata=_build_metadata(
            username=username,
            password=password,
            api_base=api_base,
            software_name=software_name,
            software_version=software_version,
            signed_xml_path=str(signed_xml),
            endpoint_contract=selected_contract,
        )
    )
    upload_response = run_browser_job(
        BrowserMcpJobRequest(
            scenario="dgii-postulacion-upload-signed-xml",
            mode="persistent_profile",
            userDataDir=str(session_dir),
            headless=headless,
            keepOpenOnFailure=keep_browser_open_on_failure,
            keepOpenOnSuccess=keep_session_open,
            target=upload_target,
            artifacts=BrowserMcpArtifacts(screenshot=True, snapshot=True, pdf=False, trace=True, saveSession=True),
            outputDir=str(run_dir),
        )
    )

    summary["signed_xml"] = str(signed_xml)
    summary["postulacion_firmado_xml"] = str(signed_xml_canonical) if signed_xml_canonical else str(signed_xml)
    summary["upload_attempted"] = True
    summary["warning_summary"] = summarize_console_warnings(_combine_artifacts(generated_response, upload_response))
    summary["upload_job"] = {
        "status": upload_response.status,
        "error": upload_response.error,
        "artifacts": upload_response.artifacts,
        "result": upload_response.result,
        "step_results": upload_response.step_results,
    }
    _apply_runtime_metadata(summary, upload_response)
    upload_auth = _extract_auth_strategy_attempted(upload_response)
    if upload_auth != "unknown":
        summary["auth_strategy_attempted"] = upload_auth
    upload_portal_auth = _extract_portal_auth_result(upload_response)
    if upload_portal_auth != "unknown":
        summary["portal_auth_result"] = upload_portal_auth
    combined_artifacts = _combine_artifacts(generated_response, upload_response)
    formulario_capture = _copy_latest_artifact(
        generated_response.artifacts,
        {".png", ".jpg", ".jpeg"},
        run_dir / "screenshot_formulario.png",
    )
    if formulario_capture is not None:
        summary["screenshot_formulario"] = str(formulario_capture)
    confirm_capture = _copy_latest_artifact(
        combined_artifacts,
        {".png", ".jpg", ".jpeg"},
        run_dir / "screenshot_confirmacion.png",
    )
    if confirm_capture is not None:
        summary["screenshot_confirmacion"] = str(confirm_capture)
    final_html = _copy_latest_artifact(combined_artifacts, {".html", ".htm"}, run_dir / "page_final.html")
    if final_html is not None:
        summary["page_final_html"] = str(final_html)

    if upload_response.status == "completed":
        set_step_state(ctx, STEP_S7, "DONE", "Envio ejecutado")
    else:
        set_step_state(ctx, STEP_S7, "ERROR", "Fallo en envio")
        add_error(
            ctx,
            step_id=STEP_S7,
            code="UPLOAD_FAILED",
            description=str(upload_response.error or "Upload scenario failed"),
        )
        summary["resume_action"] = _resume_action(summary)
        summary["resume_hint"] = "Sesion persistida en profile_dir para reintento."
        summary["root_cause"] = classify_root_cause(summary)
        if keep_session_open:
            set_step_state(ctx, STEP_S9, "WAITING_HUMAN", "Sesion abierta esperando cierre por operador")
        else:
            runtime_job_id = str(summary.get("runtime_job_id", "")).strip()
            release_attempted = False
            release_result: bool | None = None
            release_error = ""
            if summary.get("runtime_retained") and runtime_job_id:
                release_attempted = True
                try:
                    release_result = _release_retained_runtime(runtime_job_id)
                except Exception as exc:  # noqa: BLE001
                    release_result = False
                    release_error = str(exc)
                if release_result:
                    summary["runtime_retained"] = False
                    summary["browser_kept_open"] = False
            summary["runtime_release_attempted"] = release_attempted
            summary["runtime_release_result"] = release_result
            if release_error:
                summary["runtime_release_error"] = release_error
            set_step_state(ctx, STEP_S9, "DONE", "Sesion cerrada por configuracion")
        return _persist_outputs(
            run_dir=run_dir,
            summary=summary,
            ctx=ctx,
            session_started_at=session_started_at,
            session_dir=session_dir,
            mode=mode,
        )

    ok, reason = can_execute(STEP_S8, ctx)
    if not ok:
        raise RuntimeError(reason)
    set_step_state(ctx, STEP_S8, "RUNNING", "Capturando respuesta DGII")
    summary["resume_action"] = _resume_action(summary)
    summary["root_cause"] = classify_root_cause(summary)
    set_step_state(ctx, STEP_S8, "DONE", "Respuesta registrada")

    if keep_session_open:
        set_step_state(ctx, STEP_S9, "WAITING_HUMAN", "Sesion abierta esperando cierre por operador")
    else:
        runtime_job_id = str(summary.get("runtime_job_id", "")).strip()
        release_attempted = False
        release_result: bool | None = None
        release_error = ""
        if summary.get("runtime_retained") and runtime_job_id:
            release_attempted = True
            try:
                release_result = _release_retained_runtime(runtime_job_id)
            except Exception as exc:  # noqa: BLE001
                release_result = False
                release_error = str(exc)
            if release_result:
                summary["runtime_retained"] = False
                summary["browser_kept_open"] = False
        summary["runtime_release_attempted"] = release_attempted
        summary["runtime_release_result"] = release_result
        if release_error:
            summary["runtime_release_error"] = release_error
        set_step_state(ctx, STEP_S9, "DONE", "Sesion cerrada por configuracion")

    return _persist_outputs(
        run_dir=run_dir,
        summary=summary,
        ctx=ctx,
        session_started_at=session_started_at,
        session_dir=session_dir,
        mode=mode,
    )
