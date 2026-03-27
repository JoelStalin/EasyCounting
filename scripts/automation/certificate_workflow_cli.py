#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.certificate_workflow.models import IntakePayload
from app.certificate_workflow.service import build_case_artifacts, create_workflow_case, run_precheck


def _load_payload(path: Path) -> IntakePayload:
    data = json.loads(path.read_text(encoding="utf-8"))
    return IntakePayload(
        rnc=str(data.get("rnc", "")),
        razon_social=str(data.get("razon_social", "")),
        tipo_contribuyente=str(data.get("tipo_contribuyente", "")),
        delegado_nombre=str(data.get("delegado_nombre", "")),
        delegado_identificacion=str(data.get("delegado_identificacion", "")),
        delegado_correo=str(data.get("delegado_correo", "")),
        delegado_telefono=str(data.get("delegado_telefono", "")),
        delegado_cargo=str(data.get("delegado_cargo", "")),
        psc_preferida=str(data.get("psc_preferida", "")),
        usa_facturador_gratuito=bool(data.get("usa_facturador_gratuito", False)),
        ofv_habilitada=bool(data.get("ofv_habilitada", False)),
        alta_ncf_habilitada=bool(data.get("alta_ncf_habilitada", False)),
        responsable_ti=str(data.get("responsable_ti", "")),
        responsable_fiscal=str(data.get("responsable_fiscal", "")),
        ambiente_objetivo=str(data.get("ambiente_objetivo", "")),
        stack_tecnico=str(data.get("stack_tecnico", "")),
        repositorio=str(data.get("repositorio", "")),
        secret_manager=str(data.get("secret_manager", "")),
        metadata=dict(data.get("metadata", {})),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera case_id, ejecuta precheck y crea expediente de automatizacion DGII."
    )
    parser.add_argument("--input", required=True, help="JSON con datos de intake")
    parser.add_argument(
        "--output-dir",
        default="expedientes",
        help="Directorio base para el expediente de salida",
    )
    args = parser.parse_args()

    payload = _load_payload(Path(args.input))
    case = create_workflow_case(payload)
    precheck = run_precheck(case)
    case_dir = build_case_artifacts(case, precheck, base_dir=Path(args.output_dir))
    print(
        json.dumps(
            {
                "case_id": case.case_id,
                "status": precheck.status.value,
                "errors": precheck.errors,
                "warnings": precheck.warnings,
                "next_actions": precheck.next_actions,
                "case_dir": str(case_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
