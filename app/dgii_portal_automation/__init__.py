"""Automation toolkit for safe DGII portal navigation with Playwright."""

from app.dgii_portal_automation.auth import login, logout, refresh_session, validate_session
from app.dgii_portal_automation.config import DGIIAutomationConfig, ExecutionMode
from app.dgii_portal_automation.downloads import download_file, register_download, rename_by_context, validate_download
from app.dgii_portal_automation.extract import (
    extract_download_links,
    extract_fields,
    extract_messages,
    extract_table,
    normalize_data,
)
from app.dgii_portal_automation.navigation import go_to_section, resolve_menu, safe_back, wait_for_page_ready
from app.dgii_portal_automation.reporting import (
    build_csv_report,
    build_excel_report,
    build_json_report,
    generate_audit_trace,
)
from app.dgii_portal_automation.runtime import AutomationRuntime
from app.dgii_portal_automation.safety import (
    detect_sensitive_action,
    redact_secrets,
    request_confirmation,
    safe_logging,
    safe_screenshot,
)
from app.dgii_portal_automation.tasks import (
    task_busqueda_por_periodo,
    task_consulta_comprobantes,
    task_consulta_declaraciones,
    task_consulta_pagos,
    task_consulta_rnc,
    task_descarga_reportes,
    task_exportacion,
)

__all__ = [
    "AutomationRuntime",
    "DGIIAutomationConfig",
    "ExecutionMode",
    "build_csv_report",
    "build_excel_report",
    "build_json_report",
    "detect_sensitive_action",
    "download_file",
    "extract_download_links",
    "extract_fields",
    "extract_messages",
    "extract_table",
    "generate_audit_trace",
    "go_to_section",
    "login",
    "logout",
    "normalize_data",
    "redact_secrets",
    "refresh_session",
    "register_download",
    "rename_by_context",
    "request_confirmation",
    "resolve_menu",
    "safe_back",
    "safe_logging",
    "safe_screenshot",
    "task_busqueda_por_periodo",
    "task_consulta_comprobantes",
    "task_consulta_declaraciones",
    "task_consulta_pagos",
    "task_consulta_rnc",
    "task_descarga_reportes",
    "task_exportacion",
    "validate_download",
    "validate_session",
    "wait_for_page_ready",
]
