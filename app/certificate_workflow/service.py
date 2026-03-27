from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .models import IntakePayload, PrecheckResult, WorkflowCase, WorkflowStatus

DEFAULT_ALLOWED_PSC_CODES = {"AVANSI", "CCPSD", "NOVOSIT"}


def _normalize_phone(raw: str) -> str:
    return re.sub(r"\D+", "", raw or "")


def normalize_rnc(raw: str) -> str:
    return re.sub(r"\D+", "", raw or "")


def normalize_intake(payload: IntakePayload) -> IntakePayload:
    return IntakePayload(
        rnc=normalize_rnc(payload.rnc),
        razon_social=(payload.razon_social or "").strip(),
        tipo_contribuyente=(payload.tipo_contribuyente or "").strip(),
        delegado_nombre=(payload.delegado_nombre or "").strip(),
        delegado_identificacion=(payload.delegado_identificacion or "").strip(),
        delegado_correo=(payload.delegado_correo or "").strip().lower(),
        delegado_telefono=_normalize_phone(payload.delegado_telefono),
        delegado_cargo=(payload.delegado_cargo or "").strip(),
        psc_preferida=(payload.psc_preferida or "").strip().upper(),
        usa_facturador_gratuito=bool(payload.usa_facturador_gratuito),
        ofv_habilitada=bool(payload.ofv_habilitada),
        alta_ncf_habilitada=bool(payload.alta_ncf_habilitada),
        responsable_ti=(payload.responsable_ti or "").strip(),
        responsable_fiscal=(payload.responsable_fiscal or "").strip(),
        ambiente_objetivo=(payload.ambiente_objetivo or "").strip().lower(),
        stack_tecnico=(payload.stack_tecnico or "").strip(),
        repositorio=(payload.repositorio or "").strip(),
        secret_manager=(payload.secret_manager or "").strip(),
        metadata=payload.metadata,
    )


def create_case_id(now: datetime | None = None) -> str:
    instant = now or datetime.now(timezone.utc)
    return f"PSC-{instant.strftime('%Y')}-{instant.strftime('%m%d%H%M%S')}"


def create_workflow_case(payload: IntakePayload, *, case_id: str | None = None) -> WorkflowCase:
    normalized = normalize_intake(payload)
    return WorkflowCase(
        case_id=case_id or create_case_id(),
        status=WorkflowStatus.INTAKE_COMPLETED,
        payload=normalized,
    )


def run_precheck(
    workflow_case: WorkflowCase,
    *,
    allowed_psc_codes: set[str] | None = None,
) -> PrecheckResult:
    payload = workflow_case.payload
    psc_codes = allowed_psc_codes or DEFAULT_ALLOWED_PSC_CODES
    errors: list[str] = []
    warnings: list[str] = []
    next_actions: list[str] = []

    if not payload.rnc or len(payload.rnc) not in {9, 11}:
        errors.append("RNC invalido o vacio")
        next_actions.append("Completar RNC valido (9 u 11 digitos)")
    if not payload.delegado_nombre:
        errors.append("Falta nombre del delegado")
        next_actions.append("Registrar nombre completo del delegado")
    if not payload.delegado_identificacion:
        errors.append("Falta identificacion del delegado")
        next_actions.append("Registrar cedula/identificacion del delegado")
    if not payload.delegado_correo:
        errors.append("Falta correo del delegado")
        next_actions.append("Registrar correo del delegado")
    if not payload.ofv_habilitada:
        errors.append("No se ha confirmado acceso OFV")
        next_actions.append("Confirmar acceso OFV")
    if not payload.alta_ncf_habilitada:
        warnings.append("Alta NCF no confirmada")
    if payload.psc_preferida not in psc_codes:
        errors.append("PSC no definida o no autorizada")
        next_actions.append("Seleccionar PSC autorizada")
    if payload.ambiente_objetivo not in {"test", "certificacion", "produccion"}:
        errors.append("Ambiente objetivo invalido")
        next_actions.append("Definir ambiente: test/certificacion/produccion")
    if not payload.responsable_ti:
        errors.append("Falta responsable TI")
        next_actions.append("Asignar responsable TI")

    status = WorkflowStatus.PRECHECK_OK if not errors else WorkflowStatus.PRECHECK_FAILED
    return PrecheckResult(
        case_id=workflow_case.case_id,
        status=status,
        errors=errors,
        warnings=warnings,
        next_actions=next_actions,
    )


def build_case_artifacts(
    workflow_case: WorkflowCase,
    precheck: PrecheckResult,
    *,
    base_dir: Path,
) -> Path:
    case_dir = base_dir / workflow_case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "05-evidencias").mkdir(exist_ok=True)
    (case_dir / "06-seguimiento").mkdir(exist_ok=True)
    (case_dir / "07-certificado").mkdir(exist_ok=True)

    payload = workflow_case.payload
    resumen = [
        f"# Resumen {workflow_case.case_id}",
        "",
        f"- Estado: `{precheck.status.value}`",
        f"- RNC: `{payload.rnc}`",
        f"- Razon social: `{payload.razon_social}`",
        f"- Delegado: `{payload.delegado_nombre}`",
        f"- PSC preferida: `{payload.psc_preferida}`",
        f"- Ambiente objetivo: `{payload.ambiente_objetivo}`",
    ]
    if precheck.errors:
        resumen.append("- Errores precheck:")
        for item in precheck.errors:
            resumen.append(f"  - {item}")
    if precheck.warnings:
        resumen.append("- Advertencias precheck:")
        for item in precheck.warnings:
            resumen.append(f"  - {item}")
    (case_dir / "01-resumen-caso.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    (case_dir / "02-datos-contribuyente.json").write_text(
        json.dumps(
            {
                "rnc": payload.rnc,
                "razon_social": payload.razon_social,
                "tipo_contribuyente": payload.tipo_contribuyente,
                "ambiente_objetivo": payload.ambiente_objetivo,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (case_dir / "03-datos-delegado.json").write_text(
        json.dumps(
            {
                "nombre": payload.delegado_nombre,
                "identificacion": payload.delegado_identificacion,
                "correo": payload.delegado_correo,
                "telefono": payload.delegado_telefono,
                "cargo": payload.delegado_cargo,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    checklist = [
        "# Checklist documental",
        "",
        "- [ ] Evidencia de representacion o delegacion",
        "- [ ] Documento societario vigente",
        "- [ ] Documento de identidad del delegado",
        "- [ ] Comprobante del tramite con PSC",
    ]
    (case_dir / "04-checklist-documental.md").write_text("\n".join(checklist) + "\n", encoding="utf-8")
    (case_dir / "06-seguimiento" / "precheck.json").write_text(
        json.dumps(
            {
                "case_id": precheck.case_id,
                "status": precheck.status.value,
                "errors": precheck.errors,
                "warnings": precheck.warnings,
                "next_actions": precheck.next_actions,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return case_dir
