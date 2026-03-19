"""Navigation helpers for the DGII automation toolkit."""

from __future__ import annotations

import time
from typing import Any

from app.dgii_portal_automation.errors import DGIINavigationError
from app.dgii_portal_automation.safety import safe_logging
from app.dgii_portal_automation.ui import find_clickable


def wait_for_page_ready(runtime: Any, *, extra_wait_ms: int = 400) -> None:
    page = runtime.ensure_page()
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=runtime.config.navigation_timeout_ms)
    except Exception:
        pass
    page.locator("body").wait_for(state="visible")
    if extra_wait_ms > 0:
        time.sleep(extra_wait_ms / 1000)
    safe_logging(runtime, "page.ready", level="info", url=page.url)


def resolve_menu(runtime: Any, label: str) -> Any:
    page = runtime.ensure_page()
    candidate = find_clickable(page, label)
    if candidate is None:
        raise DGIINavigationError(f"No se encontro un menu o accion visible para: {label}")
    return candidate


def go_to_section(runtime: Any, *path_parts: str) -> str:
    page = runtime.ensure_page()
    if not path_parts:
        raise DGIINavigationError("Debe indicar al menos una seccion o submenu")
    for part in path_parts:
        item = resolve_menu(runtime, part)
        item.click(timeout=runtime.config.action_timeout_ms)
        wait_for_page_ready(runtime)
        safe_logging(runtime, "navigation.step", level="info", label=part, url=page.url)
    runtime.ensure_authorized_url(page.url)
    return page.url


def safe_back(runtime: Any) -> str:
    page = runtime.ensure_page()
    page.go_back(wait_until="domcontentloaded")
    wait_for_page_ready(runtime)
    runtime.ensure_authorized_url(page.url)
    safe_logging(runtime, "navigation.back", level="info", url=page.url)
    return page.url
