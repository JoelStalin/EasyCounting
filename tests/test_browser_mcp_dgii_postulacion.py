from __future__ import annotations

import json
from pathlib import Path

from app.services.browser_mcp import dgii_postulacion as dgii_postulacion_module
from app.services.browser_mcp.dgii_postulacion import (
    _build_metadata,
    _extract_auth_strategy_attempted,
    _extract_portal_auth_result,
    run_postulacion_emisor_flow,
)
from app.services.browser_mcp.schemas import BrowserMcpJobResponse


def _patch_context_layer(monkeypatch) -> dict:
    steps = [
        "S0_INIT_CONTEXT",
        "S1_LAUNCH_CHROME",
        "S2_LOGIN_OFV",
        "S3_NAVIGATE_PORTAL",
        "S4_FILL_FORM",
        "S5_GENERATE_XML",
        "S6_SIGN_XML",
        "S7_HUMAN_CONFIRM_SEND",
        "S8_CAPTURE_RESPONSE",
        "S9_CLOSE_SESSION",
    ]
    state_map = {step: "PENDING" for step in steps}
    state_map["active_errors"] = []
    context = {"session_id": "test-session", "state_map": state_map, "execution_history": []}

    def _set_step_state(ctx, step_id: str, state: str, detail: str = "") -> None:
        ctx["state_map"][step_id] = state
        ctx["execution_history"].append({"step": step_id, "state": state, "detail": detail})

    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.load_context", lambda: context)
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.bootstrap_summary_lines", lambda _ctx: [])
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.can_execute", lambda _step, _ctx: (True, ""))
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.set_step_state", _set_step_state)
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.add_error", lambda *args, **kwargs: "ERR-TEST")
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion._validate_preflight_env",
        lambda _ctx: {"missing": [], "signing_method_detected": "B_P12_OR_APP"},
    )
    return context


def test_run_postulacion_emisor_flow_orchestrates_generate_sign_upload(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DGII_REAL_USERNAME", "22500706423")
    monkeypatch.setenv("DGII_REAL_PASSWORD", "secret")
    monkeypatch.setenv("DGII_PUBLIC_API_BASE_URL", "https://api.getupsoft.com.do")
    monkeypatch.setenv("DGII_SOFTWARE_NAME", "GetUpSoft DGII e-CF API")
    monkeypatch.setenv("DGII_SOFTWARE_VERSION", "1.0")
    monkeypatch.setenv("DGII_SESSION_MODE", "direct")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_MCP", "true")
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_MCP", "true")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_TERMINAL", "YES")
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_TERMINAL", "YES")
    monkeypatch.setenv("DGII_SIGNING_P12_PATH", "C:\\fake.p12")
    monkeypatch.setenv("DGII_SIGNING_P12_PASSWORD", "secret")

    _patch_context_layer(monkeypatch)

    generated_xml = tmp_path / "generated.xml"
    generated_xml.write_text("<ECF />", encoding="utf-8")
    signed_xml = tmp_path / "generated.signed.xml"
    signed_xml.write_text("<ECF Signed='true' />", encoding="utf-8")

    responses = [
        BrowserMcpJobResponse(
            jobId="generate-job",
            status="completed",
            artifacts=[str(generated_xml)],
            result={"generatedXmlPath": str(generated_xml), "postulacionUrl": "https://ecf.dgii.gov.do/postulacion"},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
        ),
        BrowserMcpJobResponse(
            jobId="upload-job",
            status="completed",
            artifacts=[str(signed_xml)],
            result={"postulacionUrl": "https://ecf.dgii.gov.do/postulacion", "bodyPreview": "OK"},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
        ),
    ]
    captured_jobs = []

    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.ARTIFACTS_ROOT",
        tmp_path,
    )
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion._resolve_session_dir", lambda run_dir, mode: tmp_path / "session")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_test_manifest", lambda: tmp_path / "manifest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_latest_known_state", lambda summary: tmp_path / "latest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_run_note", lambda summary: tmp_path / "note.md")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.browser_policy_summary", lambda: {"compliant": True, "warnings": []})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.summarize_console_warnings", lambda artifacts: {"entries": 0})
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.run_browser_job",
        lambda _job: captured_jobs.append(_job) or responses.pop(0),
    )
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion._resolve_signed_xml_optimized",
        lambda run_dir, generated: (signed_xml, "signed_with_local_p12:test"),
    )

    summary = run_postulacion_emisor_flow()

    assert summary["generated_xml"] == str(generated_xml)
    assert summary["signed_xml"] == str(signed_xml)
    assert summary["upload_attempted"] is True
    assert summary["signature_mode"] == "signed_with_local_p12:test"
    assert summary["session_mode"] == "direct"
    assert summary["session_log"]
    assert Path(summary["session_log"]).exists()
    assert captured_jobs[1].keep_open_on_success is True
    run_summary_path = Path(summary["run_dir"]) / "run-summary.json"
    assert run_summary_path.exists()
    persisted = json.loads(run_summary_path.read_text(encoding="utf-8"))
    assert persisted["upload_job"]["status"] == "completed"


def test_run_postulacion_emisor_flow_keeps_profile_and_reports_retained_browser_on_generate_failure(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DGII_REAL_USERNAME", "22500706423")
    monkeypatch.setenv("DGII_REAL_PASSWORD", "secret")
    monkeypatch.setenv("DGII_PUBLIC_API_BASE_URL", "https://api.getupsoft.com.do")
    monkeypatch.setenv("DGII_SOFTWARE_NAME", "GetUpSoft DGII e-CF API")
    monkeypatch.setenv("DGII_SOFTWARE_VERSION", "1.0")
    monkeypatch.setenv("DGII_SIGNING_P12_PATH", "C:\\fake.p12")
    monkeypatch.setenv("DGII_SIGNING_P12_PASSWORD", "secret")
    monkeypatch.setenv("DGII_POSTULACION_KEEP_BROWSER_OPEN_ON_FAILURE", "true")
    monkeypatch.setenv("DGII_SESSION_MODE", "direct")

    _patch_context_layer(monkeypatch)

    failed = BrowserMcpJobResponse(
        jobId="generate-job",
        status="failed",
        artifacts=[],
        result={"browserRetained": True},
        networkSummary={},
        consoleSummary={},
        stepResults=[],
        error="stuck",
    )

    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.ARTIFACTS_ROOT",
        tmp_path,
    )
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion._resolve_session_dir", lambda run_dir, mode: tmp_path / "session")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_test_manifest", lambda: tmp_path / "manifest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_latest_known_state", lambda summary: tmp_path / "latest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_run_note", lambda summary: tmp_path / "note.md")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.browser_policy_summary", lambda: {"compliant": True, "warnings": []})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.summarize_console_warnings", lambda artifacts: {"entries": 0})
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.run_browser_job",
        lambda _job: failed,
    )

    summary = run_postulacion_emisor_flow()

    assert summary["stage"] == "generate_xml"
    assert summary["profile_dir"]
    assert summary["browser_kept_open"] is True
    assert summary["session_log"]
    assert Path(summary["session_log"]).exists()
    assert "Sesion" in summary["resume_hint"] or "sesion" in summary["resume_hint"].lower()


def test_build_metadata_does_not_reuse_ofv_credentials_for_portal_by_default(monkeypatch) -> None:
    monkeypatch.delenv("DGII_CERT_PORTAL_USERNAME", raising=False)
    monkeypatch.delenv("DGII_CERT_PORTAL_PASSWORD", raising=False)
    monkeypatch.setenv("DGII_PORTAL_CRED_FALLBACK", "none")

    metadata = _build_metadata(
        username="22500706423",
        password="ofv-secret",
        api_base="https://api.getupsoft.com.do",
        software_name="getupsoft",
        software_version="1.0",
    )

    assert metadata["username"] == "22500706423"
    assert metadata["password"] == "ofv-secret"
    assert metadata["portalUsername"] == ""
    assert metadata["portalPassword"] == ""
    assert metadata["portalCredentialFallback"] == "none"


def test_build_metadata_reuses_ofv_credentials_when_portal_fallback_is_ofv(monkeypatch) -> None:
    monkeypatch.delenv("DGII_CERT_PORTAL_USERNAME", raising=False)
    monkeypatch.delenv("DGII_CERT_PORTAL_PASSWORD", raising=False)
    monkeypatch.setenv("DGII_PORTAL_CRED_FALLBACK", "ofv")

    metadata = _build_metadata(
        username="22500706423",
        password="ofv-secret",
        api_base="https://api.getupsoft.com.do",
        software_name="getupsoft",
        software_version="1.0",
    )

    assert metadata["portalUsername"] == "22500706423"
    assert metadata["portalPassword"] == "ofv-secret"
    assert metadata["portalCredentialFallback"] == "ofv"


def test_run_postulacion_emisor_flow_falls_back_api_to_fe_when_endpoint_mode_auto(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DGII_REAL_USERNAME", "22500706423")
    monkeypatch.setenv("DGII_REAL_PASSWORD", "secret")
    monkeypatch.setenv("DGII_PUBLIC_API_BASE_URL", "https://api.getupsoft.com.do")
    monkeypatch.setenv("DGII_SOFTWARE_NAME", "GetUpSoft DGII e-CF API")
    monkeypatch.setenv("DGII_SOFTWARE_VERSION", "1.0")
    monkeypatch.setenv("DGII_SESSION_MODE", "direct")
    monkeypatch.setenv("DGII_ENDPOINT_MODE", "auto")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_MCP", "true")
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_MCP", "true")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_TERMINAL", "YES")
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_TERMINAL", "YES")
    monkeypatch.setenv("DGII_SIGNING_P12_PATH", "C:\\fake.p12")
    monkeypatch.setenv("DGII_SIGNING_P12_PASSWORD", "secret")

    _patch_context_layer(monkeypatch)

    generated_xml = tmp_path / "generated.xml"
    generated_xml.write_text("<ECF />", encoding="utf-8")
    signed_xml = tmp_path / "generated.signed.xml"
    signed_xml.write_text("<ECF Signed='true' />", encoding="utf-8")

    responses = [
        BrowserMcpJobResponse(
            jobId="generate-api-job",
            status="failed",
            artifacts=[],
            result={},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
            error="api contract failed",
        ),
        BrowserMcpJobResponse(
            jobId="generate-fe-job",
            status="completed",
            artifacts=[str(generated_xml)],
            result={"generatedXmlPath": str(generated_xml)},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
        ),
        BrowserMcpJobResponse(
            jobId="upload-job",
            status="completed",
            artifacts=[str(signed_xml)],
            result={"bodyPreview": "OK"},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
        ),
    ]
    captured_jobs = []

    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.ARTIFACTS_ROOT", tmp_path)
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion._resolve_session_dir", lambda run_dir, mode: tmp_path / "session")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_test_manifest", lambda: tmp_path / "manifest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_latest_known_state", lambda summary: tmp_path / "latest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_run_note", lambda summary: tmp_path / "note.md")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.browser_policy_summary", lambda: {"compliant": True, "warnings": []})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.summarize_console_warnings", lambda artifacts: {"entries": 0})
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.run_browser_job",
        lambda _job: captured_jobs.append(_job) or responses.pop(0),
    )
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion._resolve_signed_xml_optimized",
        lambda run_dir, generated: (signed_xml, "signed_with_local_p12:test"),
    )

    summary = run_postulacion_emisor_flow()

    assert summary["endpoint_contract_selected"] == "fe"
    assert captured_jobs[0].target.metadata["endpointMode"] == "api"
    assert captured_jobs[1].target.metadata["endpointMode"] == "fe"
    assert captured_jobs[2].target.metadata["endpointMode"] == "fe"


def test_run_postulacion_emisor_flow_waits_human_at_sign_without_dual_confirmation(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DGII_REAL_USERNAME", "22500706423")
    monkeypatch.setenv("DGII_REAL_PASSWORD", "secret")
    monkeypatch.setenv("DGII_PUBLIC_API_BASE_URL", "https://api.getupsoft.com.do")
    monkeypatch.setenv("DGII_SOFTWARE_NAME", "GetUpSoft DGII e-CF API")
    monkeypatch.setenv("DGII_SOFTWARE_VERSION", "1.0")
    monkeypatch.setenv("DGII_SESSION_MODE", "direct")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_MCP", "false")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_TERMINAL", "YES")
    monkeypatch.setenv("DGII_SIGNING_P12_PATH", "C:\\fake.p12")
    monkeypatch.setenv("DGII_SIGNING_P12_PASSWORD", "secret")

    context = _patch_context_layer(monkeypatch)

    generated_xml = tmp_path / "generated.xml"
    generated_xml.write_text("<ECF />", encoding="utf-8")

    responses = [
        BrowserMcpJobResponse(
            jobId="generate-job",
            status="completed",
            artifacts=[str(generated_xml)],
            result={"generatedXmlPath": str(generated_xml)},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
        ),
    ]

    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.ARTIFACTS_ROOT", tmp_path)
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion._resolve_session_dir", lambda run_dir, mode: tmp_path / "session")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_test_manifest", lambda: tmp_path / "manifest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_latest_known_state", lambda summary: tmp_path / "latest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_run_note", lambda summary: tmp_path / "note.md")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.browser_policy_summary", lambda: {"compliant": True, "warnings": []})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.summarize_console_warnings", lambda artifacts: {"entries": 0})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.run_browser_job", lambda _job: responses.pop(0))
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion._resolve_signed_xml_optimized",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("signing must not run without confirmation")),
    )

    summary = run_postulacion_emisor_flow()

    assert summary["status"] == "waiting_human"
    assert summary["root_cause"] == "waiting_human_confirmation_sign"
    assert summary["upload_attempted"] is False
    assert summary["confirmations"]["sign"]["mcp"] is False
    assert context["state_map"]["S6_SIGN_XML"] == "WAITING_HUMAN"


def test_run_postulacion_emisor_flow_waits_human_at_upload_without_dual_confirmation(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DGII_REAL_USERNAME", "22500706423")
    monkeypatch.setenv("DGII_REAL_PASSWORD", "secret")
    monkeypatch.setenv("DGII_PUBLIC_API_BASE_URL", "https://api.getupsoft.com.do")
    monkeypatch.setenv("DGII_SOFTWARE_NAME", "GetUpSoft DGII e-CF API")
    monkeypatch.setenv("DGII_SOFTWARE_VERSION", "1.0")
    monkeypatch.setenv("DGII_SESSION_MODE", "direct")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_MCP", "true")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_TERMINAL", "YES")
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_MCP", "false")
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_TERMINAL", "YES")
    monkeypatch.setenv("DGII_SIGNING_P12_PATH", "C:\\fake.p12")
    monkeypatch.setenv("DGII_SIGNING_P12_PASSWORD", "secret")

    context = _patch_context_layer(monkeypatch)

    generated_xml = tmp_path / "generated.xml"
    generated_xml.write_text("<ECF />", encoding="utf-8")
    signed_xml = tmp_path / "generated.signed.xml"
    signed_xml.write_text("<ECF Signed='true' />", encoding="utf-8")
    captured_jobs = []

    responses = [
        BrowserMcpJobResponse(
            jobId="generate-job",
            status="completed",
            artifacts=[str(generated_xml)],
            result={"generatedXmlPath": str(generated_xml)},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
        ),
    ]

    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.ARTIFACTS_ROOT", tmp_path)
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion._resolve_session_dir", lambda run_dir, mode: tmp_path / "session")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_test_manifest", lambda: tmp_path / "manifest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_latest_known_state", lambda summary: tmp_path / "latest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_run_note", lambda summary: tmp_path / "note.md")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.browser_policy_summary", lambda: {"compliant": True, "warnings": []})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.summarize_console_warnings", lambda artifacts: {"entries": 0})
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.run_browser_job",
        lambda _job: captured_jobs.append(_job) or responses.pop(0),
    )
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion._resolve_signed_xml_optimized",
        lambda run_dir, generated: (signed_xml, "signed_with_local_p12:test"),
    )

    summary = run_postulacion_emisor_flow()

    assert summary["root_cause"] == "waiting_human_confirmation_upload"
    assert summary["upload_attempted"] is False
    assert summary["confirmations"]["upload"]["mcp"] is False
    assert len(captured_jobs) == 1
    assert context["state_map"]["S7_HUMAN_CONFIRM_SEND"] == "WAITING_HUMAN"


def test_run_postulacion_emisor_flow_releases_retained_runtime_when_keep_open_disabled(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DGII_REAL_USERNAME", "22500706423")
    monkeypatch.setenv("DGII_REAL_PASSWORD", "secret")
    monkeypatch.setenv("DGII_PUBLIC_API_BASE_URL", "https://api.getupsoft.com.do")
    monkeypatch.setenv("DGII_SOFTWARE_NAME", "GetUpSoft DGII e-CF API")
    monkeypatch.setenv("DGII_SOFTWARE_VERSION", "1.0")
    monkeypatch.setenv("DGII_SESSION_MODE", "direct")
    monkeypatch.setenv("DGII_KEEP_SESSION_OPEN", "false")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_MCP", "true")
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_MCP", "true")
    monkeypatch.setenv("DGII_CONFIRM_SIGN_TERMINAL", "YES")
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_TERMINAL", "YES")
    monkeypatch.setenv("DGII_SIGNING_P12_PATH", "C:\\fake.p12")
    monkeypatch.setenv("DGII_SIGNING_P12_PASSWORD", "secret")

    context = _patch_context_layer(monkeypatch)

    generated_xml = tmp_path / "generated.xml"
    generated_xml.write_text("<ECF />", encoding="utf-8")
    signed_xml = tmp_path / "generated.signed.xml"
    signed_xml.write_text("<ECF Signed='true' />", encoding="utf-8")

    responses = [
        BrowserMcpJobResponse(
            jobId="generate-job",
            status="completed",
            artifacts=[str(generated_xml)],
            result={"generatedXmlPath": str(generated_xml), "postulacionUrl": "https://ecf.dgii.gov.do/postulacion"},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
        ),
        BrowserMcpJobResponse(
            jobId="upload-job",
            status="completed",
            artifacts=[str(signed_xml)],
            result={"postulacionUrl": "https://ecf.dgii.gov.do/postulacion", "browserRetained": True},
            networkSummary={},
            consoleSummary={},
            stepResults=[],
        ),
    ]
    released_runtime_ids: list[str] = []

    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.ARTIFACTS_ROOT", tmp_path)
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion._resolve_session_dir", lambda run_dir, mode: tmp_path / "session")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_test_manifest", lambda: tmp_path / "manifest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_latest_known_state", lambda summary: tmp_path / "latest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_run_note", lambda summary: tmp_path / "note.md")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.browser_policy_summary", lambda: {"compliant": True, "warnings": []})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.summarize_console_warnings", lambda artifacts: {"entries": 0})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.run_browser_job", lambda _job: responses.pop(0))
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion._resolve_signed_xml_optimized",
        lambda run_dir, generated: (signed_xml, "signed_with_local_p12:test"),
    )
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion._release_retained_runtime",
        lambda job_id: released_runtime_ids.append(job_id) or True,
    )

    summary = run_postulacion_emisor_flow()

    assert summary["runtime_release_attempted"] is True
    assert summary["runtime_release_result"] is True
    assert summary["runtime_retained"] is False
    assert released_runtime_ids == ["upload-job"]
    assert context["state_map"]["S9_CLOSE_SESSION"] == "DONE"


def test_extract_portal_auth_result_prioritizes_invalid_credentials_over_unknown() -> None:
    response = BrowserMcpJobResponse(
        jobId="job",
        status="failed",
        artifacts=[],
        result={},
        networkSummary={},
        consoleSummary={},
        stepResults=[
            {"name": "portal_state_probe", "status": "error", "details": {"portalAuthResult": "unknown"}},
            {"name": "portal_credentials", "status": "error", "details": {"portalAuthResult": "invalid_credentials"}},
        ],
    )

    extracted = _extract_portal_auth_result(response)

    assert extracted == "invalid_credentials"


def test_extract_auth_strategy_attempted_supports_new_step_names() -> None:
    response = BrowserMcpJobResponse(
        jobId="job",
        status="failed",
        artifacts=[],
        result={},
        networkSummary={},
        consoleSummary={},
        stepResults=[
            {"name": "ofv_session_reuse", "status": "ok", "details": {}},
            {"name": "session_reuse", "status": "error", "details": {}},
            {"name": "portal_credentials", "status": "error", "details": {}},
            {"name": "manual_seed", "status": "error", "details": {}},
        ],
    )

    extracted = _extract_auth_strategy_attempted(response)

    assert extracted == "ofv_session_reuse,session_reuse,portal_credentials,manual_seed"


def test_terminal_confirm_does_not_prompt_when_env_is_explicit_negative(monkeypatch) -> None:
    monkeypatch.setenv("DGII_CONFIRM_UPLOAD_TERMINAL", "NO")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(
        "builtins.input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("input should not be called")),
    )

    result = dgii_postulacion_module._terminal_confirm("UPLOAD")

    assert result is False
