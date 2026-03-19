"""Reusable business tasks for DGII consultation flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.dgii_portal_automation.auth import refresh_session
from app.dgii_portal_automation.downloads import download_file
from app.dgii_portal_automation.extract import snapshot_page
from app.dgii_portal_automation.models import SensitiveAction, TaskResult
from app.dgii_portal_automation.navigation import go_to_section, wait_for_page_ready
from app.dgii_portal_automation.reporting import build_csv_report, build_excel_report, build_json_report
from app.dgii_portal_automation.safety import (
    detect_sensitive_action,
    request_confirmation,
    safe_logging,
    summarize_sensitive_action,
)
from app.dgii_portal_automation.ui import find_clickable, find_input


def task_consulta_rnc(runtime: Any, rnc: str) -> TaskResult:
    refresh_session(runtime)
    _open_query_section(runtime, ["consulta", "rnc"])
    _fill_known_field(runtime, ["rnc", "cedula", "identificacion"], rnc)
    _click_search(runtime)
    extraction = snapshot_page(runtime, table_name="consulta_rnc")
    return TaskResult(
        task_name="consulta_rnc",
        url=runtime.current_url or "",
        extraction=extraction,
        metadata={"rnc": rnc},
    )


def task_consulta_comprobantes(
    runtime: Any,
    *,
    encf: str | None = None,
    fiscal_id: str | None = None,
) -> TaskResult:
    refresh_session(runtime)
    _open_query_section(runtime, ["consulta", "comprobantes"])
    if encf:
        _fill_known_field(runtime, ["encf", "ecf", "comprobante"], encf)
    if fiscal_id:
        _fill_known_field(runtime, ["rnc", "cedula", "identificacion"], fiscal_id)
    _click_search(runtime)
    extraction = snapshot_page(runtime, table_name="consulta_comprobantes")
    return TaskResult(
        task_name="consulta_comprobantes",
        url=runtime.current_url or "",
        extraction=extraction,
        metadata={"encf": encf, "fiscal_id": fiscal_id},
    )


def task_consulta_declaraciones(runtime: Any, *, desde: str | None = None, hasta: str | None = None) -> TaskResult:
    refresh_session(runtime)
    _open_query_section(runtime, ["consulta", "declaraciones"])
    _fill_period(runtime, desde=desde, hasta=hasta)
    _click_search(runtime)
    extraction = snapshot_page(runtime, table_name="consulta_declaraciones")
    return TaskResult(
        task_name="consulta_declaraciones",
        url=runtime.current_url or "",
        extraction=extraction,
        metadata={"desde": desde, "hasta": hasta},
    )


def task_consulta_pagos(runtime: Any, *, desde: str | None = None, hasta: str | None = None) -> TaskResult:
    refresh_session(runtime)
    _open_query_section(runtime, ["consulta", "pagos"])
    _fill_period(runtime, desde=desde, hasta=hasta)
    _click_search(runtime)
    extraction = snapshot_page(runtime, table_name="consulta_pagos")
    return TaskResult(
        task_name="consulta_pagos",
        url=runtime.current_url or "",
        extraction=extraction,
        metadata={"desde": desde, "hasta": hasta},
    )


def task_descarga_reportes(runtime: Any, *, label: str = "descargar", context: dict[str, str] | None = None) -> TaskResult:
    refresh_session(runtime)
    artifact = download_file(runtime, trigger_label=label, context=context)
    extraction = snapshot_page(runtime, table_name="descarga_reportes", paginate=False)
    return TaskResult(
        task_name="descarga_reportes",
        url=runtime.current_url or "",
        extraction=extraction,
        downloads=[artifact],
        metadata={"label": label, "context": context or {}},
    )


def task_busqueda_por_periodo(
    runtime: Any,
    *,
    section_terms: list[str],
    desde: str | None = None,
    hasta: str | None = None,
) -> TaskResult:
    refresh_session(runtime)
    _open_query_section(runtime, section_terms)
    _fill_period(runtime, desde=desde, hasta=hasta)
    _click_search(runtime)
    extraction = snapshot_page(runtime, table_name="_".join(section_terms))
    return TaskResult(
        task_name="busqueda_por_periodo",
        url=runtime.current_url or "",
        extraction=extraction,
        metadata={"section_terms": section_terms, "desde": desde, "hasta": hasta},
    )


def task_exportacion(runtime: Any, result: TaskResult, *, basename: str) -> dict[str, Path]:
    rows = result.extraction.tables[0].rows if result.extraction.tables else []
    base_path = runtime.config.export_dir / basename
    exported = {
        "json": build_json_report(result, base_path.with_suffix(".json"), indent=runtime.config.export.json_indent),
    }
    if rows:
        exported["csv"] = build_csv_report(rows, base_path.with_suffix(".csv"), encoding=runtime.config.export.csv_encoding)
        exported["xlsx"] = build_excel_report(
            rows,
            base_path.with_suffix(".xlsx"),
            sheet_name=runtime.config.export.excel_sheet_name,
        )
    safe_logging(
        runtime,
        "task.export",
        level="info",
        task_name=result.task_name,
        exports={key: str(value) for key, value in exported.items()},
    )
    return exported


def prepare_sensitive_action_summary(label: str | None, *, runtime: Any, details: dict[str, Any] | None = None) -> dict[str, Any] | None:
    action = detect_sensitive_action(label, current_url=runtime.current_url, details=details)
    if action is None:
        return None
    return summarize_sensitive_action(action)


def maybe_confirm_sensitive_click(
    runtime: Any,
    *,
    label: str,
    confirmation_callback: Any | None = None,
) -> SensitiveAction | None:
    action = detect_sensitive_action(label, current_url=runtime.current_url)
    if action is None:
        return None
    request_confirmation(action, mode=runtime.config.mode, confirmation_callback=confirmation_callback)
    return action


def _open_query_section(runtime: Any, section_terms: list[str]) -> None:
    go_to_section(runtime, section_terms)
    wait_for_page_ready(runtime)


def _fill_known_field(runtime: Any, terms: list[str], value: str) -> None:
    page = runtime.ensure_page()
    for term in terms:
        locator = find_input(page, term)
        if locator is not None:
            locator.fill(value, timeout=runtime.config.action_timeout_ms)
            safe_logging(runtime, "task.fill_field", level="info", field_hint=term)
            return
    safe_logging(runtime, "task.fill_field.missed", level="warning", hints=terms)


def _fill_period(runtime: Any, *, desde: str | None, hasta: str | None) -> None:
    if desde:
        _fill_known_field(runtime, ["desde", "fecha desde", "periodo desde"], desde)
    if hasta:
        _fill_known_field(runtime, ["hasta", "fecha hasta", "periodo hasta"], hasta)


def _click_search(runtime: Any) -> None:
    page = runtime.ensure_page()
    for term in ["consultar", "buscar", "filtrar", "ver"]:
        locator = find_clickable(page, term)
        if locator is None:
            continue
        action = detect_sensitive_action(term, current_url=runtime.current_url)
        if action is not None:
            request_confirmation(action, mode=runtime.config.mode)
        locator.first.click(timeout=runtime.config.action_timeout_ms)
        wait_for_page_ready(runtime)
        safe_logging(runtime, "task.search_clicked", level="info", trigger=term)
        return
    safe_logging(runtime, "task.search_missing", level="warning", url=runtime.current_url)
