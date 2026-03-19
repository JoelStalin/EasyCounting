"""CLI wrapper for DGII portal automation tasks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from app.dgii_portal_automation.auth import login, logout
from app.dgii_portal_automation.config import DGIIAutomationConfig
from app.dgii_portal_automation.reporting import generate_audit_trace
from app.dgii_portal_automation.runtime import AutomationRuntime
from app.dgii_portal_automation.tasks import (
    task_busqueda_por_periodo,
    task_consulta_comprobantes,
    task_consulta_declaraciones,
    task_consulta_pagos,
    task_consulta_rnc,
    task_descarga_reportes,
    task_exportacion,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automatizacion segura del portal DGII con Playwright")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("login-check", help="Valida autenticacion y sesion en DGII")

    consulta_rnc = subparsers.add_parser("consulta-rnc", help="Consulta RNC o cedula")
    consulta_rnc.add_argument("--value", required=True)

    comprobantes = subparsers.add_parser("consulta-comprobantes", help="Consulta comprobantes")
    comprobantes.add_argument("--encf")
    comprobantes.add_argument("--fiscal-id")

    declaraciones = subparsers.add_parser("consulta-declaraciones", help="Lista declaraciones")
    declaraciones.add_argument("--desde")
    declaraciones.add_argument("--hasta")

    pagos = subparsers.add_parser("consulta-pagos", help="Lista pagos")
    pagos.add_argument("--desde")
    pagos.add_argument("--hasta")

    reportes = subparsers.add_parser("descarga-reportes", help="Descarga reporte visible")
    reportes.add_argument("--label", default="descargar")

    periodo = subparsers.add_parser("busqueda-por-periodo", help="Busqueda generica por periodo")
    periodo.add_argument("--section", action="append", required=True)
    periodo.add_argument("--desde")
    periodo.add_argument("--hasta")

    exportar = subparsers.add_parser("exportar-json", help="Exporta una consulta de comprobantes")
    exportar.add_argument("--basename", required=True)
    exportar.add_argument("--encf")
    exportar.add_argument("--fiscal-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = DGIIAutomationConfig.from_env()
    with AutomationRuntime(config) as runtime:
        login(runtime)
        try:
            result: Any = None
            if args.command == "login-check":
                result = {"authenticated": True, "url": runtime.current_url}
            elif args.command == "consulta-rnc":
                result = task_consulta_rnc(runtime, args.value)
            elif args.command == "consulta-comprobantes":
                result = task_consulta_comprobantes(runtime, encf=args.encf, fiscal_id=args.fiscal_id)
            elif args.command == "consulta-declaraciones":
                result = task_consulta_declaraciones(runtime, desde=args.desde, hasta=args.hasta)
            elif args.command == "consulta-pagos":
                result = task_consulta_pagos(runtime, desde=args.desde, hasta=args.hasta)
            elif args.command == "descarga-reportes":
                result = task_descarga_reportes(runtime, label=args.label)
            elif args.command == "busqueda-por-periodo":
                result = task_busqueda_por_periodo(runtime, section_terms=args.section, desde=args.desde, hasta=args.hasta)
            elif args.command == "exportar-json":
                task_result = task_consulta_comprobantes(runtime, encf=args.encf, fiscal_id=args.fiscal_id)
                result = task_exportacion(runtime, task_result, basename=args.basename)
            else:  # pragma: no cover - argparse enforces
                parser.error(f"Comando no soportado: {args.command}")
            audit_path = generate_audit_trace(runtime, runtime.config.audit_dir / "dgii_audit_trace.json")
            print({"result": _printable(result), "audit_trace": str(audit_path)})
            return 0
        finally:
            logout(runtime)


def _printable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _printable(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "__dict__"):
        return {key: _printable(item) for key, item in value.__dict__.items()}
    return value


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
