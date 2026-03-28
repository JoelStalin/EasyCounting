from __future__ import annotations

import json
from pathlib import Path

from app.services.browser_mcp.dgii_postulacion import _build_metadata, run_postulacion_emisor_flow
from app.services.browser_mcp.schemas import BrowserMcpJobResponse


def test_run_postulacion_emisor_flow_orchestrates_generate_sign_upload(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DGII_REAL_USERNAME", "22500706423")
    monkeypatch.setenv("DGII_REAL_PASSWORD", "secret")
    monkeypatch.setenv("DGII_PUBLIC_API_BASE_URL", "https://api.getupsoft.com.do")
    monkeypatch.setenv("DGII_SOFTWARE_NAME", "GetUpSoft DGII e-CF API")
    monkeypatch.setenv("DGII_SOFTWARE_VERSION", "1.0")

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

    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.ARTIFACTS_ROOT",
        tmp_path,
    )
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.ensure_profile_clone",
        lambda: {
            "profileDir": str(tmp_path / "profile"),
            "sourceProfile": "Default",
            "bootstrapped": True,
            "bootstrapManifestPath": str(tmp_path / "profile" / "_dgii_profile_bootstrap.json"),
        },
    )
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_test_manifest", lambda: tmp_path / "manifest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_latest_known_state", lambda summary: tmp_path / "latest.json")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.write_run_note", lambda summary: tmp_path / "note.md")
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.browser_policy_summary", lambda: {"compliant": True, "warnings": []})
    monkeypatch.setattr("app.services.browser_mcp.dgii_postulacion.summarize_console_warnings", lambda artifacts: {"entries": 0})
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.run_browser_job",
        lambda _job: responses.pop(0),
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
    run_summary_path = Path(summary["run_dir"]) / "run-summary.json"
    assert run_summary_path.exists()
    persisted = json.loads(run_summary_path.read_text(encoding="utf-8"))
    assert persisted["upload_job"]["status"] == "completed"


def test_run_postulacion_emisor_flow_keeps_profile_and_reports_retained_browser_on_generate_failure(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DGII_REAL_USERNAME", "22500706423")
    monkeypatch.setenv("DGII_REAL_PASSWORD", "secret")
    monkeypatch.setenv("DGII_POSTULACION_KEEP_BROWSER_OPEN_ON_FAILURE", "true")

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
    monkeypatch.setattr(
        "app.services.browser_mcp.dgii_postulacion.ensure_profile_clone",
        lambda: {
            "profileDir": str(tmp_path / "profile"),
            "sourceProfile": "Default",
            "bootstrapped": True,
            "bootstrapManifestPath": str(tmp_path / "profile" / "_dgii_profile_bootstrap.json"),
        },
    )
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
    assert "profile_dir" in summary["resume_hint"]


def test_build_metadata_does_not_reuse_ofv_credentials_for_portal_by_default(monkeypatch) -> None:
    monkeypatch.delenv("DGII_CERT_PORTAL_USERNAME", raising=False)
    monkeypatch.delenv("DGII_CERT_PORTAL_PASSWORD", raising=False)

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
