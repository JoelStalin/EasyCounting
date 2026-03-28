from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

CONTEXT_PATH = Path(".ai_context/notes/DGII_SESSION_CONTEXT.json")
STEP_SEQUENCE = [
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _initial_state_map() -> dict[str, object]:
    state_map: dict[str, object] = {step: "PENDING" for step in STEP_SEQUENCE}
    state_map["active_errors"] = []
    return state_map


def _fresh_context() -> dict[str, object]:
    return {
        "schema_version": "3.0",
        "last_updated": _now_iso(),
        "session_id": str(uuid4()),
        "state_map": _initial_state_map(),
        "execution_history": [],
        "prompt_modifications": [],
        "technical_decisions": [],
        "test_results": {
            "unit": {"last_run": None, "passed": 0, "failed": 0, "log": None},
            "functional": {"last_run": None, "passed": 0, "failed": 0, "log": None},
            "e2e": {"last_run": None, "passed": 0, "failed": 0, "log": None},
            "regression": [],
        },
        "env_vars_present": [],
        "artifacts": {
            "session_dir": None,
            "xml_generated": None,
            "xml_signed": None,
            "xml_sha256": None,
            "screenshots": [],
            "run_summary": None,
        },
        "operator_notes": [],
    }


def load_context() -> dict[str, object]:
    if not CONTEXT_PATH.exists():
        ctx = _fresh_context()
        save_context(ctx)
        return ctx
    raw = CONTEXT_PATH.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    parsed.setdefault("state_map", _initial_state_map())
    parsed["state_map"].setdefault("active_errors", [])
    return parsed


def save_context(ctx: dict[str, object]) -> None:
    ctx["last_updated"] = _now_iso()
    CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT_PATH.write_text(json.dumps(ctx, ensure_ascii=False, indent=2), encoding="utf-8")


def active_errors(ctx: dict[str, object]) -> list[dict[str, object]]:
    state_map = ctx.get("state_map", {})
    errors = state_map.get("active_errors", [])
    if not isinstance(errors, list):
        return []
    return [item for item in errors if isinstance(item, dict) and item.get("status") != "RESOLVED"]


def can_execute(step_id: str, ctx: dict[str, object]) -> tuple[bool, str]:
    if step_id not in STEP_SEQUENCE:
        return False, f"Paso desconocido: {step_id}"
    idx = STEP_SEQUENCE.index(step_id)
    if idx == 0:
        return True, ""
    prev = STEP_SEQUENCE[idx - 1]
    state_map = ctx.get("state_map", {})
    prev_state = str(state_map.get(prev, "PENDING"))
    if prev_state not in {"DONE", "SKIPPED_BY_OPERATOR"}:
        return False, f"El paso anterior '{prev}' está en '{prev_state}'. Debe estar en DONE."
    errors = active_errors(ctx)
    if errors:
        ids = [str(item.get("id", "unknown")) for item in errors]
        return False, f"Hay errores activos sin resolver: {ids}"
    return True, ""


def append_history(ctx: dict[str, object], step_id: str, state: str, detail: str = "") -> None:
    history = ctx.setdefault("execution_history", [])
    if isinstance(history, list):
        history.append(
            {
                "timestamp": _now_iso(),
                "step": step_id,
                "state": state,
                "detail": detail,
            }
        )


def set_step_state(ctx: dict[str, object], step_id: str, state: str, detail: str = "") -> None:
    state_map = ctx.setdefault("state_map", _initial_state_map())
    state_map[step_id] = state
    append_history(ctx, step_id, state, detail)
    save_context(ctx)


def add_error(
    ctx: dict[str, object],
    *,
    step_id: str,
    code: str,
    description: str,
    stack: str = "",
    screenshot: str = "",
) -> str:
    error_id = f"ERR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{code}"
    state_map = ctx.setdefault("state_map", _initial_state_map())
    active = state_map.setdefault("active_errors", [])
    if isinstance(active, list):
        active.append(
            {
                "id": error_id,
                "step": step_id,
                "code": code,
                "description": description,
                "stack": stack,
                "screenshot": screenshot,
                "status": "ACTIVE",
                "investigation": "",
                "solution": "",
            }
        )
    set_step_state(ctx, step_id, "ERROR", f"Error registrado: {error_id}")
    return error_id


def resolve_error(ctx: dict[str, object], error_id: str, *, cause: str, solution: str) -> bool:
    state_map = ctx.get("state_map", {})
    errors = state_map.get("active_errors", [])
    if not isinstance(errors, list):
        return False
    resolved = False
    for error in errors:
        if not isinstance(error, dict):
            continue
        if error.get("id") != error_id:
            continue
        error["status"] = "RESOLVED"
        error["causa_raiz"] = cause
        error["solution"] = solution
        error["resolved_at"] = _now_iso()
        resolved = True
    if resolved:
        save_context(ctx)
    return resolved


def resolve_active_errors(ctx: dict[str, object], *, cause: str, solution: str) -> int:
    state_map = ctx.get("state_map", {})
    errors = state_map.get("active_errors", [])
    if not isinstance(errors, list):
        return 0
    resolved_count = 0
    for error in errors:
        if not isinstance(error, dict):
            continue
        if error.get("status") == "RESOLVED":
            continue
        error["status"] = "RESOLVED"
        error["causa_raiz"] = cause
        error["solution"] = solution
        error["resolved_at"] = _now_iso()
        resolved_count += 1
    if resolved_count:
        save_context(ctx)
    return resolved_count


def mark_skipped_by_operator(ctx: dict[str, object], step_id: str, reason: str) -> None:
    set_step_state(ctx, step_id, "SKIPPED_BY_OPERATOR", f"Operador: {reason}")


def bootstrap_summary_lines(ctx: dict[str, object]) -> list[str]:
    state_map = ctx.get("state_map", {})
    step_states = {step: state_map.get(step, "PENDING") for step in STEP_SEQUENCE}
    errors = active_errors(ctx)
    lines = [
        f"[CONTEXTO] Sesion: {ctx.get('session_id')}",
        f"[CONTEXTO] Pasos: {step_states}",
        f"[CONTEXTO] Errores activos: {len(errors)}",
    ]
    for err in errors:
        lines.append(f"  - {err.get('id')}: {err.get('description')}")
    return lines
