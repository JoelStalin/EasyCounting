from __future__ import annotations

from pathlib import Path

from app.services.browser_mcp import dgii_context


def test_context_can_execute_blocks_when_previous_step_not_done(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(dgii_context, "CONTEXT_PATH", tmp_path / "DGII_SESSION_CONTEXT.json")
    ctx = dgii_context.load_context()

    ok, reason = dgii_context.can_execute("S2_LOGIN_OFV", ctx)

    assert ok is False
    assert "S1_LAUNCH_CHROME" in reason


def test_context_add_error_blocks_next_step(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(dgii_context, "CONTEXT_PATH", tmp_path / "DGII_SESSION_CONTEXT.json")
    ctx = dgii_context.load_context()
    dgii_context.set_step_state(ctx, "S0_INIT_CONTEXT", "DONE", "ok")
    dgii_context.set_step_state(ctx, "S1_LAUNCH_CHROME", "DONE", "ok")

    error_id = dgii_context.add_error(
        ctx,
        step_id="S2_LOGIN_OFV",
        code="LOGIN_FAILED",
        description="Credenciales invalidas",
    )
    ok, reason = dgii_context.can_execute("S3_NAVIGATE_PORTAL", ctx)

    assert error_id.startswith("ERR-")
    assert ok is False
    assert "S2_LOGIN_OFV" in reason
    assert "ERROR" in reason


def test_context_resolve_error_unblocks_following_steps(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(dgii_context, "CONTEXT_PATH", tmp_path / "DGII_SESSION_CONTEXT.json")
    ctx = dgii_context.load_context()
    dgii_context.set_step_state(ctx, "S0_INIT_CONTEXT", "DONE", "ok")
    dgii_context.set_step_state(ctx, "S1_LAUNCH_CHROME", "DONE", "ok")
    dgii_context.set_step_state(ctx, "S2_LOGIN_OFV", "DONE", "ok")

    error_id = dgii_context.add_error(
        ctx,
        step_id="S3_NAVIGATE_PORTAL",
        code="PORTAL_FAIL",
        description="portal",
    )
    resolved = dgii_context.resolve_error(ctx, error_id, cause="manual", solution="retry")
    dgii_context.set_step_state(ctx, "S3_NAVIGATE_PORTAL", "DONE", "retry ok")
    ok, _ = dgii_context.can_execute("S4_FILL_FORM", ctx)

    assert resolved is True
    assert ok is True
