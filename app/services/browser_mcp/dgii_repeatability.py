from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.services.browser_mcp.client import build_browser_mcp_settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS_ROOT = PROJECT_ROOT / "tests" / "artifacts"
DOCS_ROOT = PROJECT_ROOT / "docs" / "certificados" / "autoasistido"
RUN_NOTES_ROOT = DOCS_ROOT / "run_notes"
MANIFEST_PATH = DOCS_ROOT / "dgii_postulacion_test_manifest.json"
LATEST_STATE_PATH = DOCS_ROOT / "latest_known_state.json"
DEFAULT_PROFILE_CLONE_ROOT = ARTIFACTS_ROOT / "_profile_clones" / "dgii_postulacion_browser_mcp"
DEFAULT_SOURCE_PROFILE = "Default"
DEFAULT_POLICY_BASELINE = "strict_normal_browser"
DEFAULT_AUTH_STRATEGIES = ["session_reuse", "portal_credentials", "manual_seed"]
PROFILE_MANIFEST_NAME = "_dgii_profile_bootstrap.json"
NON_BLOCKING_CONSOLE_PATTERNS = (
    "feature-policy",
    "permissions-policy",
    "unrecognized feature",
)
PROFILE_COPY_IGNORE_NAMES = {
    "cache",
    "code cache",
    "gpucache",
    "grshadercache",
    "dawncache",
    "shadercache",
    "crashpad",
    "component_crx_cache",
    "extensions_crx_cache",
    "safe browsing",
    "optimizationhints",
    "subresource filter",
    "browsermetrics",
    "deferredbrowsermetrics",
    "media cache",
}


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _parse_bool(raw: str | None, default: bool) -> bool:
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(raw: str | None, default: list[str]) -> list[str]:
    if raw is None or not raw.strip():
        return list(default)
    values = [item.strip().lower() for item in raw.split(",") if item.strip()]
    return values or list(default)


def session_mode() -> str:
    raw = os.getenv("DGII_SESSION_MODE", "").strip().lower()
    if raw in {"direct", "profile_clone"}:
        return raw
    return "direct"


def _chrome_user_data_dir() -> Path:
    raw = os.getenv("DGII_CHROME_USER_DATA_DIR", "").strip()
    if raw:
        return Path(raw)
    local_appdata = os.getenv("LOCALAPPDATA", "").strip()
    if not local_appdata:
        raise RuntimeError("No se pudo resolver LOCALAPPDATA para ubicar el perfil real de Chrome")
    return Path(local_appdata) / "Google" / "Chrome" / "User Data"


def _source_profile_name() -> str:
    raw = os.getenv("DGII_CHROME_PROFILE_SOURCE", "").strip()
    return raw or DEFAULT_SOURCE_PROFILE


def _clone_root() -> Path:
    raw = os.getenv("DGII_POSTULACION_PROFILE_CLONE_ROOT", "").strip()
    if raw:
        path = Path(raw)
    else:
        path = DEFAULT_PROFILE_CLONE_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def _profile_dir() -> Path:
    raw = os.getenv("DGII_POSTULACION_PROFILE_DIR", "").strip()
    if raw:
        path = Path(raw)
    else:
        slug = _source_profile_name().replace(" ", "_").lower()
        path = _clone_root() / f"{slug}_working"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _policy_baseline() -> str:
    raw = os.getenv("DGII_POSTULACION_POLICY_BASELINE", "").strip()
    return raw or DEFAULT_POLICY_BASELINE


def load_auth_strategies() -> list[str]:
    allowed = {"session_reuse", "portal_credentials", "manual_seed"}
    values = _parse_csv(os.getenv("DGII_POSTULACION_AUTH_STRATEGIES", ""), DEFAULT_AUTH_STRATEGIES)
    normalized = [item for item in values if item in allowed]
    return normalized or list(DEFAULT_AUTH_STRATEGIES)


def manual_seed_timeout_seconds() -> int:
    raw = os.getenv("DGII_POSTULACION_MANUAL_SEED_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return 60
    try:
        value = int(raw)
    except ValueError:
        return 60
    return min(max(value, 10), 900)


def browser_policy_summary() -> dict[str, object]:
    config = build_browser_mcp_settings()
    warnings: list[str] = []
    try:
        viewport_width = int(os.getenv("BROWSER_MCP_VIEWPORT_WIDTH", "1440") or "1440")
    except ValueError:
        viewport_width = 1440
    try:
        viewport_height = int(os.getenv("BROWSER_MCP_VIEWPORT_HEIGHT", "900") or "900")
    except ValueError:
        viewport_height = 900
    if config.default_browser != "chromium":
        warnings.append("browser_not_chromium")
    user_agent = (os.getenv("BROWSER_MCP_USER_AGENT", "") or "").strip()
    if user_agent:
        warnings.append("custom_user_agent_configured")
    proxy = (os.getenv("BROWSER_MCP_PROXY_SERVER", "") or "").strip()
    if proxy:
        warnings.append("custom_proxy_configured")
    return {
        "baseline": _policy_baseline(),
        "browser": config.default_browser,
        "headlessDefault": config.default_headless,
        "viewport": {
            "width": viewport_width,
            "height": viewport_height,
        },
        "userAgentOverride": user_agent,
        "proxyServer": proxy,
        "compliant": not warnings,
        "warnings": warnings,
    }


def _ignore_profile_entry(name: str) -> bool:
    lowered = name.lower()
    if lowered in PROFILE_COPY_IGNORE_NAMES:
        return True
    return lowered.startswith("singleton") or lowered.endswith(".tmp") or lowered == "lockfile"


def _copy_profile_tree(source: Path, target: Path) -> list[dict[str, str]]:
    def _ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if _ignore_profile_entry(name)}

    copy_warnings: list[dict[str, str]] = []
    try:
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=_ignore)
    except shutil.Error as exc:
        errors = exc.args[0] if exc.args else []
        for src, dst, message in errors:
            copy_warnings.append(
                {
                    "source": str(src),
                    "target": str(dst),
                    "error": str(message),
                }
            )
    return copy_warnings


def _write_profile_manifest(target_root: Path, payload: dict[str, object]) -> Path:
    path = target_root / PROFILE_MANIFEST_NAME
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def ensure_profile_clone() -> dict[str, object]:
    source_user_data_dir = _chrome_user_data_dir()
    source_profile = _source_profile_name()
    profile_dir = _profile_dir()
    source_profile_dir = source_user_data_dir / source_profile
    if not source_profile_dir.exists():
        raise RuntimeError(f"No existe el perfil de Chrome configurado: {source_profile_dir}")

    manifest_path = profile_dir / PROFILE_MANIFEST_NAME
    default_profile_dir = profile_dir / "Default"
    needs_bootstrap = not manifest_path.exists() or not default_profile_dir.exists()

    if needs_bootstrap:
        shutil.rmtree(profile_dir, ignore_errors=True)
        profile_dir.mkdir(parents=True, exist_ok=True)
        local_state = source_user_data_dir / "Local State"
        if local_state.exists():
            shutil.copy2(local_state, profile_dir / "Local State")
        source_preferences = source_profile_dir / "Preferences"
        copy_warnings = _copy_profile_tree(source_profile_dir, default_profile_dir)
        manifest = {
            "bootstrappedAt": datetime.now().isoformat(),
            "sourceUserDataDir": str(source_user_data_dir),
            "sourceProfile": source_profile,
            "sourceProfileDir": str(source_profile_dir),
            "targetProfileDir": str(profile_dir),
            "policyBaseline": _policy_baseline(),
            "sourcePreferencesExists": source_preferences.exists(),
            "ignoredNames": sorted(PROFILE_COPY_IGNORE_NAMES),
            "copyWarnings": copy_warnings[:100],
        }
        manifest_path = _write_profile_manifest(profile_dir, manifest)
        if not (default_profile_dir / "Preferences").exists():
            raise RuntimeError(
                f"No se pudo bootstrappear el perfil de Chrome para DGII; falta Preferences en {default_profile_dir}"
            )
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    return {
        "profileDir": str(profile_dir),
        "sourceUserDataDir": str(source_user_data_dir),
        "sourceProfile": source_profile,
        "bootstrapManifestPath": str(manifest_path),
        "bootstrapped": needs_bootstrap,
    }


def build_test_manifest() -> dict[str, object]:
    mode = session_mode()
    if mode == "profile_clone":
        opening_step = "profile_clone_bootstrap"
    else:
        opening_step = "direct_session_bootstrap"
    return {
        "version": "2026-03-27.repeatable-baseline.v1",
        "policyBaseline": _policy_baseline(),
        "sessionMode": mode,
        "sourceProfile": _source_profile_name(),
        "steps": [
            opening_step,
            "ofv_session_reuse",
            "portal_state_probe",
            "portal_credentials_attempt",
            "manual_seed_hold",
            "form_fill_and_generate",
            "sign_xml",
            "upload_signed_xml",
            "dgii_response_classification",
        ],
        "authStrategies": load_auth_strategies(),
        "manualSeedTimeoutSeconds": manual_seed_timeout_seconds(),
        "notes": "Warnings Feature-Policy/Permissions-Policy se registran como warning_non_blocking salvo evidencia funcional.",
    }


def write_test_manifest() -> Path:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(build_test_manifest(), ensure_ascii=False, indent=2), encoding="utf-8")
    return MANIFEST_PATH


def _collect_console_entries(artifacts: list[str]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for artifact in artifacts:
        path = Path(artifact)
        if path.name != "console.jsonl" or not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                parsed = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                entries.append(parsed)
    return entries


def summarize_console_warnings(artifacts: list[str]) -> dict[str, object]:
    entries = _collect_console_entries(artifacts)
    non_blocking: list[dict[str, object]] = []
    other: list[dict[str, object]] = []
    for entry in entries:
        text = str(entry.get("text", "")).lower()
        if any(pattern in text for pattern in NON_BLOCKING_CONSOLE_PATTERNS):
            non_blocking.append(entry)
        elif str(entry.get("type", "")).lower() in {"warning", "error"}:
            other.append(entry)
    return {
        "entries": len(entries),
        "nonBlockingWarnings": len(non_blocking),
        "otherWarnings": len(other),
        "nonBlockingSamples": non_blocking[:3],
        "otherSamples": other[:3],
    }


def classify_root_cause(summary: dict[str, object]) -> str:
    portal_auth_result = str(summary.get("portal_auth_result", "")).strip().lower()
    if portal_auth_result == "invalid_credentials":
        return "portal_credentials_invalid"

    upload_job = summary.get("upload_job")
    if isinstance(upload_job, dict):
        upload_result = upload_job.get("result")
        if isinstance(upload_result, dict):
            body_preview = str(upload_result.get("bodyPreview", "")).lower()
            if "firma inválida" in body_preview or "firma invalida" in body_preview:
                diagnostics = summary.get("identity_diagnostics")
                if isinstance(diagnostics, dict):
                    warnings = diagnostics.get("warnings")
                    if isinstance(warnings, list) and "certificate_subject_missing_representative_rnc" in warnings:
                        return "certificate_identity_mismatch"
                return "signature_invalid"
            if "versionsoftware" in body_preview:
                return "version_software_invalid"

    error_text = str(summary.get("error", "")).lower()
    if "autenticación fallida" in error_text or "credenciales proporcionadas no son válidas" in error_text:
        return "portal_credentials_invalid"
    if "firma inválida" in error_text or "firma invalida" in error_text:
        return "signature_invalid"
    if "versionsoftware" in error_text:
        return "version_software_invalid"
    if "portal de certificacion abierto pero no se detecto formulario" in error_text:
        return "portal_navigation_stuck"
    return "unknown"


def write_latest_known_state(summary: dict[str, object]) -> Path:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "updatedAt": datetime.now().isoformat(),
        "sessionMode": summary.get("session_mode", session_mode()),
        "rootCause": summary.get("root_cause"),
        "runtimeRetained": summary.get("runtime_retained"),
        "currentUrl": summary.get("current_url"),
        "profileDir": summary.get("profile_dir"),
        "sourceProfile": summary.get("profile_source"),
        "authStrategyAttempted": summary.get("auth_strategy_attempted"),
        "portalAuthResult": summary.get("portal_auth_result"),
        "runDir": summary.get("run_dir"),
        "resumeAction": summary.get("resume_action"),
    }
    LATEST_STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return LATEST_STATE_PATH


def write_run_note(summary: dict[str, object]) -> Path:
    RUN_NOTES_ROOT.mkdir(parents=True, exist_ok=True)
    note_path = RUN_NOTES_ROOT / f"{_timestamp()}_dgii_postulacion.md"
    warning_summary = summary.get("warning_summary") or {}
    content = "\n".join(
        [
            "# DGII Postulacion Run Note",
            "",
            f"- Timestamp: {datetime.now().isoformat()}",
            f"- Run dir: {summary.get('run_dir')}",
            f"- Session mode: {summary.get('session_mode', session_mode())}",
            f"- Profile source: {summary.get('profile_source')}",
            f"- Profile dir: {summary.get('profile_dir')}",
            f"- Runtime job id: {summary.get('runtime_job_id')}",
            f"- Runtime retained: {summary.get('runtime_retained')}",
            f"- Current URL: {summary.get('current_url')}",
            f"- Auth strategy attempted: {summary.get('auth_strategy_attempted')}",
            f"- Portal auth result: {summary.get('portal_auth_result')}",
            f"- Root cause: {summary.get('root_cause')}",
            f"- Resume action: {summary.get('resume_action')}",
            "",
            "## Warning summary",
            "",
            "```json",
            json.dumps(warning_summary, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    note_path.write_text(f"{content}\n", encoding="utf-8")
    return note_path

