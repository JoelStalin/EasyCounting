"""Structured extraction helpers for DGII portal pages."""

from __future__ import annotations

from typing import Any

from app.dgii_portal_automation.errors import DGIIExtractionError
from app.dgii_portal_automation.models import DownloadLink, ExtractionResult, StructuredTable
from app.dgii_portal_automation.navigation import wait_for_page_ready
from app.dgii_portal_automation.safety import safe_logging
from app.dgii_portal_automation.ui import find_clickable, visible_text


def extract_table(
    runtime: Any,
    *,
    table_name: str | None = None,
    paginate: bool = True,
    max_pages: int | None = None,
) -> StructuredTable:
    page = runtime.ensure_page()
    wait_for_page_ready(runtime)
    tables = page.locator("table:visible")
    try:
        count = tables.count()
    except Exception as exc:  # pragma: no cover - UI dependent
        raise DGIIExtractionError("No fue posible enumerar tablas visibles") from exc
    if count == 0:
        raise DGIIExtractionError("No se encontro ninguna tabla visible en la pagina")

    table = tables.first
    headers = _table_headers(table)
    rows: list[dict[str, str]] = []
    pages_read = 0
    max_pages = max_pages or runtime.config.max_table_pages

    while True:
        pages_read += 1
        rows.extend(_table_rows(table, headers))
        if not paginate or pages_read >= max_pages:
            break
        next_button = _find_next_button(page)
        if next_button is None:
            break
        disabled = _is_disabled(next_button)
        if disabled:
            break
        before = len(rows)
        next_button.click(timeout=runtime.config.action_timeout_ms)
        wait_for_page_ready(runtime)
        rows.extend(_table_rows(table, headers))
        after = len(rows)
        if after == before:
            break

    safe_logging(
        runtime,
        "extract.table",
        level="info",
        table_name=table_name,
        headers=headers,
        rows=len(rows),
        pages_read=pages_read,
    )
    return StructuredTable(name=table_name, rows=rows, headers=headers, pages_read=pages_read)


def extract_fields(runtime: Any) -> dict[str, str]:
    page = runtime.ensure_page()
    wait_for_page_ready(runtime)
    values: dict[str, str] = {}

    labels = page.locator("label:visible")
    try:
        count = min(labels.count(), 200)
    except Exception as exc:  # pragma: no cover - UI dependent
        raise DGIIExtractionError("No fue posible leer las etiquetas visibles") from exc

    for index in range(count):
        label = labels.nth(index)
        label_text = visible_text(label)
        if not label_text:
            continue
        target_id = label.get_attribute("for")
        if target_id:
            field = page.locator(f"#{target_id}")
            if field.count():
                field_value = _read_field_value(field.first)
                if field_value:
                    values[label_text] = field_value

    fields = page.locator("input:visible, select:visible, textarea:visible")
    try:
        field_count = min(fields.count(), 200)
    except Exception as exc:  # pragma: no cover - UI dependent
        raise DGIIExtractionError("No fue posible leer los campos visibles") from exc

    for index in range(field_count):
        field = fields.nth(index)
        name = (
            field.get_attribute("aria-label")
            or field.get_attribute("name")
            or field.get_attribute("id")
            or f"field_{index + 1}"
        )
        if name in values:
            continue
        field_value = _read_field_value(field)
        if field_value:
            values[name] = field_value

    safe_logging(runtime, "extract.fields", level="info", field_count=len(values))
    return values


def extract_messages(runtime: Any) -> list[str]:
    page = runtime.ensure_page()
    selectors = [
        "[role='alert']:visible",
        "[aria-live]:visible",
        ".alert:visible",
        ".toast:visible",
        ".message:visible",
        ".messages:visible",
    ]
    messages: list[str] = []
    seen: set[str] = set()
    for selector in selectors:
        locator = page.locator(selector)
        try:
            count = min(locator.count(), 50)
        except Exception:
            continue
        for index in range(count):
            text = visible_text(locator.nth(index))
            normalized = normalize_data(text)
            if normalized and normalized not in seen:
                seen.add(normalized)
                messages.append(normalized)
    safe_logging(runtime, "extract.messages", level="info", message_count=len(messages))
    return messages


def extract_download_links(runtime: Any) -> list[DownloadLink]:
    page = runtime.ensure_page()
    terms = ["descargar", "export", "excel", "csv", "pdf", "acuse", "reporte"]
    links: list[DownloadLink] = []
    seen: set[tuple[str | None, str | None]] = set()
    for term in terms:
        locator = find_clickable(page, term)
        if locator is None:
            continue
        try:
            count = min(locator.count(), 20)
        except Exception:
            count = 1
        for index in range(count):
            item = locator.nth(index)
            text = normalize_data(visible_text(item)) or term
            href = item.get_attribute("href")
            key = (text, href)
            if key in seen:
                continue
            seen.add(key)
            links.append(DownloadLink(label=text, url=href, selector_hint=term))
    safe_logging(runtime, "extract.download_links", level="info", count=len(links))
    return links


def normalize_data(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.replace("\xa0", " ").split()).strip()


def snapshot_page(runtime: Any, *, table_name: str | None = None, paginate: bool = True) -> ExtractionResult:
    tables: list[StructuredTable] = []
    try:
        tables.append(extract_table(runtime, table_name=table_name, paginate=paginate))
    except DGIIExtractionError:
        pass
    return ExtractionResult(
        url=runtime.current_url or "",
        tables=tables,
        fields=extract_fields(runtime),
        messages=extract_messages(runtime),
        download_links=extract_download_links(runtime),
    )


def _table_headers(table: Any) -> list[str]:
    headers: list[str] = []
    header_cells = table.locator("thead tr:visible th:visible")
    try:
        header_count = header_cells.count()
    except Exception:
        header_count = 0
    if header_count == 0:
        header_cells = table.locator("tr:visible").first.locator("th:visible, td:visible")
        try:
            header_count = header_cells.count()
        except Exception:
            header_count = 0
    for index in range(header_count):
        text = normalize_data(visible_text(header_cells.nth(index)))
        headers.append(text or f"col_{index + 1}")
    return headers or ["col_1"]


def _table_rows(table: Any, headers: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    body_rows = table.locator("tbody tr:visible")
    try:
        row_count = body_rows.count()
    except Exception:
        row_count = 0
    if row_count == 0:
        body_rows = table.locator("tr:visible")
        try:
            row_count = body_rows.count()
        except Exception:
            row_count = 0
    for row_index in range(row_count):
        row = body_rows.nth(row_index)
        cells = row.locator("td:visible, th:visible")
        try:
            cell_count = cells.count()
        except Exception:
            cell_count = 0
        if cell_count == 0:
            continue
        rows.append(
            {
                headers[cell_index] if cell_index < len(headers) else f"col_{cell_index + 1}": normalize_data(
                    visible_text(cells.nth(cell_index))
                )
                for cell_index in range(cell_count)
            }
        )
    return rows


def _find_next_button(page: Any) -> Any | None:
    for term in ["siguiente", "next", ">", ">>"]:
        locator = find_clickable(page, term)
        if locator is not None:
            return locator.first
    return None


def _is_disabled(locator: Any) -> bool:
    try:
        return bool(locator.is_disabled())
    except Exception:
        pass
    classes = (locator.get_attribute("class") or "").lower()
    aria_disabled = (locator.get_attribute("aria-disabled") or "").lower()
    return "disabled" in classes or aria_disabled == "true"


def _read_field_value(locator: Any) -> str:
    try:
        input_value = locator.input_value(timeout=1000)
    except Exception:
        input_value = None
    if input_value:
        return normalize_data(input_value)
    text = visible_text(locator)
    if text:
        return normalize_data(text)
    try:
        value_attr = locator.get_attribute("value")
    except Exception:
        value_attr = None
    return normalize_data(value_attr)
