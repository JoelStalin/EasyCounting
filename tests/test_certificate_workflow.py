from __future__ import annotations

import json

from app.certificate_workflow.models import IntakePayload, WorkflowStatus
from app.certificate_workflow.service import build_case_artifacts, create_workflow_case, run_precheck


def _valid_payload() -> IntakePayload:
    return IntakePayload(
        rnc="131-23456-7",
        razon_social="Empresa Demo SRL",
        tipo_contribuyente="juridica",
        delegado_nombre="Juan Perez",
        delegado_identificacion="00112345678",
        delegado_correo="Juan.Perez@empresa.com",
        delegado_telefono="+1 (809) 555-1234",
        delegado_cargo="Gerente",
        psc_preferida="avansi",
        usa_facturador_gratuito=False,
        ofv_habilitada=True,
        alta_ncf_habilitada=True,
        responsable_ti="ti@empresa.com",
        responsable_fiscal="fiscal@empresa.com",
        ambiente_objetivo="test",
    )


def test_precheck_ok_for_valid_payload(tmp_path) -> None:
    case = create_workflow_case(_valid_payload())
    result = run_precheck(case)
    assert result.status == WorkflowStatus.PRECHECK_OK
    assert result.errors == []
    case_dir = build_case_artifacts(case, result, base_dir=tmp_path)
    assert (case_dir / "01-resumen-caso.md").exists()
    payload = json.loads((case_dir / "02-datos-contribuyente.json").read_text(encoding="utf-8"))
    assert payload["rnc"] == "131234567"


def test_precheck_fails_when_required_data_missing() -> None:
    payload = _valid_payload()
    payload.ofv_habilitada = False
    payload.psc_preferida = "INVALIDA"
    payload.responsable_ti = ""
    payload.ambiente_objetivo = "local"
    result = run_precheck(create_workflow_case(payload))
    assert result.status == WorkflowStatus.PRECHECK_FAILED
    assert "No se ha confirmado acceso OFV" in result.errors
    assert "PSC no definida o no autorizada" in result.errors
    assert "Falta responsable TI" in result.errors
    assert "Ambiente objetivo invalido" in result.errors

