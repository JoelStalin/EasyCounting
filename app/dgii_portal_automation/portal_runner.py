"""Unified auto-assisted portal runner for Selenium/Playwright."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.dgii_portal_automation.config import DGIIAutomationConfig
from app.dgii_portal_automation.runtime import AutomationRuntime
from app.dgii_portal_automation.tasks import (
    task_consulta_comprobantes,
    task_consulta_rnc,
)


@dataclass(slots=True)
class PortalTaskResult:
    task_name: str
    case_id: str
    execution_id: str
    engine: str
    status: str
    current_step: str
    message: str
    artifacts: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def run_portal_task(
    task_name: str,
    case_id: str,
    execution_id: str,
    input_payload: dict[str, Any],
    *,
    engine: str = "selenium",
) -> PortalTaskResult:
    engine_value = (engine or "selenium").strip().lower()
    if engine_value == "selenium":
        return _run_with_selenium(task_name, case_id, execution_id, input_payload)
    if engine_value == "playwright":
        return _run_with_playwright(task_name, case_id, execution_id, input_payload)
    return PortalTaskResult(
        task_name=task_name,
        case_id=case_id,
        execution_id=execution_id,
        engine=engine_value,
        status="FAILED_BLOCKED",
        current_step=task_name,
        message=f"Motor no soportado: {engine_value}",
        details={"supported_engines": ["selenium", "playwright"]},
    )


def _run_with_selenium(task_name: str, case_id: str, execution_id: str, payload: dict[str, Any]) -> PortalTaskResult:
    if task_name != "postulacion_full":
        return PortalTaskResult(
            task_name=task_name,
            case_id=case_id,
            execution_id=execution_id,
            engine="selenium",
            status="FAILED_BLOCKED",
            current_step=task_name,
            message="Selenium runner solo soporta task 'postulacion_full' en esta version",
        )

    script = Path("scripts/automation/run_real_dgii_postulacion_ofv.py")
    if not script.exists():
        return PortalTaskResult(
            task_name=task_name,
            case_id=case_id,
            execution_id=execution_id,
            engine="selenium",
            status="FAILED_BLOCKED",
            current_step=task_name,
            message="Script Selenium no encontrado",
            details={"script": str(script)},
        )

    env = dict(**payload.get("env", {}))
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        env={**os.environ, **env},
    )
    if proc.returncode != 0:
        return PortalTaskResult(
            task_name=task_name,
            case_id=case_id,
            execution_id=execution_id,
            engine="selenium",
            status="FAILED_RETRYABLE",
            current_step=task_name,
            message="Error ejecutando Selenium postulacion",
            details={"returncode": proc.returncode, "stderr_tail": proc.stderr[-2500:]},
        )
    raw = (proc.stdout or "").strip().splitlines()
    parsed: dict[str, Any] = {}
    if raw:
        try:
            parsed = json.loads(raw[-1])
        except json.JSONDecodeError:
            parsed = {"stdout_tail": proc.stdout[-2500:]}
    artifacts: list[str] = []
    run_dir = parsed.get("run_dir")
    if isinstance(run_dir, str) and run_dir:
        artifacts.append(run_dir)
    return PortalTaskResult(
        task_name=task_name,
        case_id=case_id,
        execution_id=execution_id,
        engine="selenium",
        status="OK",
        current_step="SUBMIT_DONE",
        message="Selenium postulacion ejecutada",
        artifacts=artifacts,
        details=parsed,
    )


def _run_with_playwright(task_name: str, case_id: str, execution_id: str, payload: dict[str, Any]) -> PortalTaskResult:
    # Auto-assisted policy: sensitive/legal actions pause for human approval.
    if task_name in {"portal_login", "form_fill", "upload", "submit"} and payload.get("requires_human", False):
        return PortalTaskResult(
            task_name=task_name,
            case_id=case_id,
            execution_id=execution_id,
            engine="playwright",
            status="FAILED_BLOCKED",
            current_step="HUMAN_APPROVAL_PENDING",
            message="Paso sensible requiere aprobacion humana",
            details={"hint": "Resolver CAPTCHA/confirmacion legal y reanudar"},
        )

    config = DGIIAutomationConfig.from_env()
    with AutomationRuntime(config) as runtime:
        if task_name == "consulta_rnc":
            rnc = str(payload.get("rnc") or "").strip()
            if not rnc:
                return PortalTaskResult(
                    task_name=task_name,
                    case_id=case_id,
                    execution_id=execution_id,
                    engine="playwright",
                    status="FAILED_BLOCKED",
                    current_step=task_name,
                    message="Falta rnc en input_payload",
                )
            result = task_consulta_rnc(runtime, rnc)
            return PortalTaskResult(
                task_name=task_name,
                case_id=case_id,
                execution_id=execution_id,
                engine="playwright",
                status="OK",
                current_step=task_name,
                message="Consulta RNC completada",
                details=asdict(result),
            )
        if task_name == "consulta_comprobantes":
            result = task_consulta_comprobantes(
                runtime,
                encf=payload.get("encf"),
                fiscal_id=payload.get("fiscal_id"),
            )
            return PortalTaskResult(
                task_name=task_name,
                case_id=case_id,
                execution_id=execution_id,
                engine="playwright",
                status="OK",
                current_step=task_name,
                message="Consulta comprobantes completada",
                details=asdict(result),
            )
    return PortalTaskResult(
        task_name=task_name,
        case_id=case_id,
        execution_id=execution_id,
        engine="playwright",
        status="FAILED_BLOCKED",
        current_step=task_name,
        message=f"Task Playwright no implementada: {task_name}",
    )
