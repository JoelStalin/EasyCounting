from __future__ import annotations

import json
from pathlib import Path

from app.services.browser_mcp import dgii_repeatability
from app.services.browser_mcp.dgii_repeatability import (
    classify_root_cause,
    ensure_profile_clone,
    summarize_console_warnings,
    write_latest_known_state,
    write_run_note,
)


def test_ensure_profile_clone_bootstraps_from_real_chrome_profile(monkeypatch, tmp_path: Path) -> None:
    source_user_data = tmp_path / "chrome-user-data"
    source_profile = source_user_data / "Default"
    source_profile.mkdir(parents=True)
    (source_user_data / "Local State").write_text('{"browser":{"enabled_labs_experiments":[]}}', encoding="utf-8")
    (source_profile / "Preferences").write_text('{"profile":{"name":"JOEL STALIN"}}', encoding="utf-8")
    target_profile = tmp_path / "working-profile"

    monkeypatch.setenv("DGII_CHROME_USER_DATA_DIR", str(source_user_data))
    monkeypatch.setenv("DGII_CHROME_PROFILE_SOURCE", "Default")
    monkeypatch.setenv("DGII_POSTULACION_PROFILE_DIR", str(target_profile))
    monkeypatch.setenv("DGII_POSTULACION_POLICY_BASELINE", "strict_normal_browser")

    result = ensure_profile_clone()

    assert result["bootstrapped"] is True
    assert (target_profile / "Local State").exists()
    assert (target_profile / "Default" / "Preferences").exists()
    manifest = json.loads((target_profile / "_dgii_profile_bootstrap.json").read_text(encoding="utf-8"))
    assert manifest["sourceProfile"] == "Default"
    assert manifest["policyBaseline"] == "strict_normal_browser"


def test_summarize_console_warnings_marks_feature_policy_as_non_blocking(tmp_path: Path) -> None:
    console_artifact = tmp_path / "console.jsonl"
    console_artifact.write_text(
        "\n".join(
            [
                json.dumps({"type": "warning", "text": "Error with Feature-Policy header: Unrecognized feature: 'true'."}),
                json.dumps({"type": "warning", "text": "Another warning"}),
            ]
        ),
        encoding="utf-8",
    )

    summary = summarize_console_warnings([str(console_artifact)])

    assert summary["entries"] == 2
    assert summary["nonBlockingWarnings"] == 1
    assert summary["otherWarnings"] == 1


def test_repeatability_state_and_note_capture_portal_credentials_invalid(
    monkeypatch,
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs"
    run_notes_root = docs_root / "run_notes"
    latest_state_path = docs_root / "latest_known_state.json"

    monkeypatch.setattr(dgii_repeatability, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(dgii_repeatability, "RUN_NOTES_ROOT", run_notes_root)
    monkeypatch.setattr(dgii_repeatability, "LATEST_STATE_PATH", latest_state_path)

    summary = {
        "run_dir": "tests/artifacts/example-run",
        "profile_dir": "tests/artifacts/_persistent_sessions/dgii",
        "profile_source": "Default",
        "runtime_job_id": "browser-job-123",
        "runtime_retained": False,
        "current_url": "https://ecf.dgii.gov.do/CerteCF/PortalCertificacion/Login/SignIn",
        "auth_strategy_attempted": "portal_credentials",
        "portal_auth_result": "invalid_credentials",
        "resume_action": "retry_with_same_manifest",
        "warning_summary": {"nonBlockingWarnings": 1, "otherWarnings": 0},
    }
    summary["root_cause"] = classify_root_cause(summary)

    latest_path = write_latest_known_state(summary)
    run_note_path = write_run_note(summary)

    assert summary["root_cause"] == "portal_credentials_invalid"
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest_payload["rootCause"] == "portal_credentials_invalid"
    assert latest_payload["authStrategyAttempted"] == "portal_credentials"
    assert run_note_path.exists()
    run_note_text = run_note_path.read_text(encoding="utf-8")
    assert "portal_credentials_invalid" in run_note_text
    assert "portal_credentials" in run_note_text
