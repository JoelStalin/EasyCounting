from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from app.infra.settings import settings
from app.security.signing import get_certificate_metadata, sign_xml_enveloped, validate_signed_xml_details
from app.security.xml_dsig import SigningOptions
from app.services.browser_mcp.client import build_browser_mcp_settings
from app.services.browser_mcp.dgii_repeatability import (
    ARTIFACTS_ROOT,
    browser_policy_summary,
    classify_root_cause,
    ensure_profile_clone,
    load_auth_strategies,
    manual_seed_timeout_seconds,
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


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


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
    raw = os.getenv("DGII_POSTULACION_PROFILE_DIR", "").strip()
    if raw:
        path = Path(raw)
    else:
        path = DEFAULT_PROFILE_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def _keep_browser_open_on_failure(headless: bool) -> bool:
    if headless:
        return False
    raw = os.getenv("DGII_POSTULACION_KEEP_BROWSER_OPEN_ON_FAILURE", "").strip().lower()
    if raw:
        return raw in {"1", "true", "yes", "on"}
    try:
        return build_browser_mcp_settings().mode == "remote"
    except Exception:  # noqa: BLE001
        return False


def _build_metadata(
    *,
    username: str,
    password: str,
    api_base: str,
    software_name: str,
    software_version: str,
    signed_xml_path: str | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "username": username,
        "password": password,
        "portalUsername": os.getenv("DGII_CERT_PORTAL_USERNAME", "").strip(),
        "portalPassword": os.getenv("DGII_CERT_PORTAL_PASSWORD", "").strip(),
        "apiBase": api_base.rstrip("/"),
        "softwareName": software_name,
        "softwareVersion": software_version,
        "authStrategies": load_auth_strategies(),
        "manualSeedTimeoutSeconds": manual_seed_timeout_seconds(),
        "policyBaseline": os.getenv("DGII_POSTULACION_POLICY_BASELINE", "").strip() or "strict_normal_browser",
    }
    pause_before_generate_seconds = os.getenv("DGII_POSTULACION_PAUSE_BEFORE_GENERATE_SECONDS", "").strip()
    if pause_before_generate_seconds:
        metadata["pauseBeforeGenerateSeconds"] = pause_before_generate_seconds
    if signed_xml_path:
        metadata["signedXmlPath"] = signed_xml_path
    return metadata


def _load_signing_order() -> list[str]:
    raw = os.getenv(
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
    request_code = os.getenv("DGII_VIAFIRMA_REQUEST_CODE", "").strip()
    if request_code:
        from scripts.automation.viafirma_download import redownload_viafirma_certificate

        downloaded = redownload_viafirma_certificate(request_code, output_dir=run_dir / "viafirma")
        password = os.getenv("DGII_SIGNING_P12_PASSWORD", "").strip() or settings.dgii_effective_pfx_password or None
        return downloaded, password, f"viafirma:{request_code}"

    p12_path_raw = os.getenv("DGII_SIGNING_P12_PATH", "").strip() or settings.dgii_effective_pfx_path
    if not p12_path_raw:
        return None, None, "missing"
    password = os.getenv("DGII_SIGNING_P12_PASSWORD", "").strip() or settings.dgii_effective_pfx_password or None
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
            signed_path_raw = os.getenv("DGII_POSTULACION_SIGNED_XML_PATH", "").strip()
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
    for step in response.step_results:
        details = step.get("details") or {}
        if not isinstance(details, dict):
            continue
        value = details.get("portalAuthResult")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown"


def _extract_auth_strategy_attempted(response: BrowserMcpJobResponse | None) -> str:
    if response is None:
        return "not_attempted"
    preferred_names = {
        "ofv_session_reuse",
        "portal_state_probe",
        "portal_credentials_attempt",
        "manual_seed_hold",
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


def run_postulacion_emisor_flow() -> dict[str, object]:
    username = os.getenv("DGII_REAL_USERNAME", "").strip()
    password = os.getenv("DGII_REAL_PASSWORD", "").strip()
    if not username or not password:
        raise RuntimeError("Faltan DGII_REAL_USERNAME y DGII_REAL_PASSWORD")

    write_test_manifest()
    api_base = os.getenv("DGII_PUBLIC_API_BASE_URL", DEFAULT_API_BASE).strip() or DEFAULT_API_BASE
    software_name = os.getenv("DGII_SOFTWARE_NAME", DEFAULT_SOFTWARE_NAME).strip() or DEFAULT_SOFTWARE_NAME
    software_version = _normalize_software_version(os.getenv("DGII_SOFTWARE_VERSION", DEFAULT_SOFTWARE_VERSION))
    headless = (os.getenv("DGII_PORTAL_HEADLESS", "").strip().lower() in {"1", "true", "yes", "on"})
    keep_browser_open_on_failure = _keep_browser_open_on_failure(headless)
    run_dir = ARTIFACTS_ROOT / f"{_timestamp()}_dgii_postulacion_browser_mcp"
    run_dir.mkdir(parents=True, exist_ok=True)
    profile_bootstrap = ensure_profile_clone()
    profile_dir = Path(str(profile_bootstrap["profileDir"]))
    warning_summary = {}
    generated_response: BrowserMcpJobResponse | None = None
    upload_response: BrowserMcpJobResponse | None = None

    common_target = BrowserMcpTarget(
        metadata=_build_metadata(
            username=username,
            password=password,
            api_base=api_base,
            software_name=software_name,
            software_version=software_version,
        )
    )

    generated_response = run_browser_job(
        BrowserMcpJobRequest(
            scenario="dgii-postulacion-generate-xml",
            mode="persistent_profile",
            userDataDir=str(profile_dir),
            headless=headless,
            keepOpenOnFailure=keep_browser_open_on_failure,
            target=common_target,
            artifacts=BrowserMcpArtifacts(screenshot=True, snapshot=True, pdf=False, trace=True, saveSession=False),
            outputDir=str(run_dir),
        )
    )
    warning_summary = summarize_console_warnings(generated_response.artifacts)
    if generated_response.status != "completed":
        runtime_metadata = _runtime_metadata(generated_response)
        summary = {
            "run_dir": str(run_dir),
            "stage": "generate_xml",
            "status": generated_response.status,
            "error": generated_response.error,
            "artifacts": generated_response.artifacts,
            "profile_dir": str(profile_dir),
            "profile_source": profile_bootstrap["sourceProfile"],
            "profile_bootstrap": profile_bootstrap,
            "policy_baseline": browser_policy_summary(),
            "warning_summary": warning_summary,
            "auth_strategy_attempted": _extract_auth_strategy_attempted(generated_response),
            "portal_auth_result": _extract_portal_auth_result(generated_response),
            **runtime_metadata,
            "browser_kept_open": runtime_metadata["runtime_retained"],
            "resume_action": _resume_action(
                {
                    "runtime_retained": runtime_metadata["runtime_retained"],
                    "profile_dir": str(profile_dir),
                }
            ),
            "resume_hint": (
                "La sesion persistente queda en profile_dir; si browser_kept_open=true, la ventana tambien quedo abierta."
            ),
        }
        summary["root_cause"] = classify_root_cause(summary)
        (run_dir / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        write_latest_known_state(summary)
        note_path = write_run_note(summary)
        summary["run_note_path"] = str(note_path)
        (run_dir / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return summary

    generated_xml = _find_generated_xml(generated_response.artifacts, generated_response.result)
    if generated_xml is None or not generated_xml.exists():
        raise RuntimeError("No fue posible localizar el XML generado por la postulacion")

    signed_xml, signature_mode = _resolve_signed_xml_optimized(run_dir, generated_xml)
    summary: dict[str, object] = {
        "run_dir": str(run_dir),
        "profile_dir": str(profile_dir),
        "profile_source": profile_bootstrap["sourceProfile"],
        "profile_bootstrap": profile_bootstrap,
        "policy_baseline": browser_policy_summary(),
        "generated_xml": str(generated_xml),
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
    }
    p12_path, p12_password, p12_source = _resolve_p12_source(run_dir)
    summary["p12_source"] = p12_source
    if p12_path and p12_path.exists():
        try:
            summary["identity_diagnostics"] = _postulacion_identity_diagnostics(generated_xml, p12_path, p12_password)
        except Exception as exc:  # noqa: BLE001
            summary["identity_diagnostics_error"] = str(exc)

    if signed_xml is None:
        summary["upload_attempted"] = False
        summary["next_required"] = (
            "Provide DGII_POSTULACION_SIGNED_XML_PATH or DGII_SIGNING_P12_PATH + DGII_SIGNING_P12_PASSWORD"
        )
        summary.update(_runtime_metadata(generated_response))
        summary["warning_summary"] = summarize_console_warnings(_combine_artifacts(generated_response))
        summary["resume_action"] = _resume_action(summary)
        summary["root_cause"] = classify_root_cause(summary)
        (run_dir / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        write_latest_known_state(summary)
        note_path = write_run_note(summary)
        summary["run_note_path"] = str(note_path)
        (run_dir / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return summary

    upload_target = BrowserMcpTarget(
        metadata=_build_metadata(
            username=username,
            password=password,
            api_base=api_base,
            software_name=software_name,
            software_version=software_version,
            signed_xml_path=str(signed_xml),
        )
    )
    upload_response = run_browser_job(
        BrowserMcpJobRequest(
            scenario="dgii-postulacion-upload-signed-xml",
            mode="persistent_profile",
            userDataDir=str(profile_dir),
            headless=headless,
            keepOpenOnFailure=keep_browser_open_on_failure,
            target=upload_target,
            artifacts=BrowserMcpArtifacts(screenshot=True, snapshot=True, pdf=False, trace=True, saveSession=False),
            outputDir=str(run_dir),
        )
    )

    summary["signed_xml"] = str(signed_xml)
    summary["upload_attempted"] = True
    summary["warning_summary"] = summarize_console_warnings(_combine_artifacts(generated_response, upload_response))
    summary["upload_job"] = {
        "status": upload_response.status,
        "error": upload_response.error,
        "artifacts": upload_response.artifacts,
        "result": upload_response.result,
        "step_results": upload_response.step_results,
    }
    summary.update(_runtime_metadata(upload_response))
    summary["browser_kept_open"] = bool(upload_response.result.get("browserRetained")) if isinstance(upload_response.result, dict) else False
    upload_auth = _extract_auth_strategy_attempted(upload_response)
    if upload_auth != "unknown":
        summary["auth_strategy_attempted"] = upload_auth
    upload_portal_auth = _extract_portal_auth_result(upload_response)
    if upload_portal_auth != "unknown":
        summary["portal_auth_result"] = upload_portal_auth
    summary["resume_action"] = _resume_action(summary)
    if upload_response.status != "completed":
        summary["resume_hint"] = (
            "La sesion persistente se conserva en profile_dir; si browser_kept_open=true, retoma desde la ventana abierta."
        )
    summary["root_cause"] = classify_root_cause(summary)
    (run_dir / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_latest_known_state(summary)
    note_path = write_run_note(summary)
    summary["run_note_path"] = str(note_path)
    (run_dir / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
