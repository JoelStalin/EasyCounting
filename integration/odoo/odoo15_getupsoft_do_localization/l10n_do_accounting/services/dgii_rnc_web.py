# -*- coding: utf-8 -*-
"""Official DGII RNC/Cedula lookup helpers for Odoo localization.

All network errors, HTTP 404s and 'not found' responses are handled
silently: they return None / [] so callers can let the user type freely.
"""

from __future__ import annotations

import difflib
import logging
import re
from html import unescape
from urllib.error import URLError

try:
    import requests
    from bs4 import BeautifulSoup
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    requests = None
    BeautifulSoup = None

_logger = logging.getLogger(__name__)

DGII_RNC_LOOKUP_URL = (
    "https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/rnc.aspx"
)
DEFAULT_TIMEOUT = 12

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "es-DO,es;q=0.9,en;q=0.8",
    "Referer": "https://dgii.gov.do/",
}

_FORM_FIELD_NAMES = (
    "__VIEWSTATE",
    "__VIEWSTATEGENERATOR",
    "__EVENTVALIDATION",
)

# Expose these so callers can catch them even without importing urllib
class HTTPError(Exception):
    pass


# ─────────────────────────── helpers ─────────────────────────────────────────

def normalize_fiscal_id(value):
    """Strip non-digits; return the result only if it is 9 or 11 chars long."""
    digits = re.sub(r"[^0-9]", "", value or "")
    return digits if len(digits) in (9, 11) else ""


def _clean_html_text(fragment):
    fragment = re.sub(r"<br\s*/?>", " | ", str(fragment), flags=re.IGNORECASE)
    fragment = re.sub(r"&nbsp;", " ", str(fragment), flags=re.IGNORECASE)
    fragment = re.sub(r"<[^>]+>", " ", str(fragment))
    return re.sub(r"\s+", " ", unescape(str(fragment))).strip()


def _score_similarity(query, candidate):
    """Return 0.0-1.0 fuzzy match ratio between two strings (case-insensitive)."""
    q = query.upper().strip()
    c = candidate.upper().strip()
    return difflib.SequenceMatcher(None, q, c).ratio()


def _sort_by_similarity(query, results, name_key="name", threshold=0.0):
    """Sort result list by similarity to query. Discard items below threshold."""
    scored = []
    for item in results:
        candidate = item.get(name_key) or item.get("commercial_name") or ""
        score = _score_similarity(query, candidate)
        if score >= threshold:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


# ─────────────────────────── form-state scraping ─────────────────────────────

def _get_session():
    if not _HAS_REQUESTS:
        raise ImportError("'requests' library is not installed in this environment")
    s = requests.Session()
    s.headers.update(_BROWSER_HEADERS)
    return s


def extract_form_state(html_text):
    """Extract ASP.NET hidden form tokens from HTML."""
    state = {}
    if _HAS_REQUESTS and BeautifulSoup:
        soup = BeautifulSoup(html_text, 'html.parser')
        for field_name in _FORM_FIELD_NAMES:
            inp = soup.find('input', {'name': field_name})
            if inp:
                state[field_name] = inp.get('value', '')
    else:
        for field_name in _FORM_FIELD_NAMES:
            m = re.search(
                r'name="%s"[^>]*value="([^"]*)"' % re.escape(field_name),
                html_text, flags=re.IGNORECASE,
            )
            if m:
                state[field_name] = unescape(m.group(1))
    return state


# ─────────────────────────── parsers ─────────────────────────────────────────

def parse_lookup_result(html_text, fiscal_id=None):
    """Parse a single-contributor result table. Returns dict or None."""
    if not html_text:
        return None

    if _HAS_REQUESTS and BeautifulSoup:
        soup = BeautifulSoup(html_text, 'html.parser')

        # Non-blocking: just return None if 'no encontrado'
        info_label = soup.find(id='cphMain_lblInformacion')
        if info_label:
            msg = info_label.text.lower()
            if any(k in msg for k in ('no se encuentra inscrito', 'no se encontr', 'verifique')):
                _logger.debug("DGII: contribuyente no encontrado – omitiendo")
                return None

        table = soup.find('table', id='cphMain_dvDatosContribuyentes')
        if not table:
            return None

        cells = table.find_all('td')
        if len(cells) < 4:
            return None

        fields = {}
        for i in range(0, len(cells) - 1, 2):
            key = cells[i].text.rstrip(':').strip()
            if key:
                fields[key] = cells[i + 1].text.strip()
    else:
        # Regex fallback
        m = re.search(
            r'<span[^>]*id="cphMain_lblInformacion"[^>]*>(.*?)</span>',
            html_text, flags=re.IGNORECASE | re.DOTALL,
        )
        if m:
            msg = _clean_html_text(m.group(1)).lower()
            if any(k in msg for k in ('no se encuentra inscrito', 'no se encontr', 'verifique')):
                return None

        table_m = re.search(
            r'<table[^>]*id="cphMain_dvDatosContribuyentes"[^>]*>(.*?)</table>',
            html_text, flags=re.IGNORECASE | re.DOTALL,
        )
        if not table_m:
            return None

        cells = [_clean_html_text(c) for c in
                 re.findall(r"<td[^>]*>(.*?)</td>", table_m.group(1),
                            flags=re.IGNORECASE | re.DOTALL)]
        fields = {}
        for i in range(0, len(cells) - 1, 2):
            key = (cells[i] or "").rstrip(":").strip()
            if key:
                fields[key] = cells[i + 1].strip()

    name = fields.get("Nombre/Razón Social", "")
    if not name:
        return None

    extracted_rnc = fields.get("Cédula/RNC", "")
    actual_fiscal_id = re.sub(r"[^0-9]", "", extracted_rnc or fiscal_id or "")

    commercial_name = fields.get("Nombre Comercial") or name
    category = fields.get("Categoría", "")
    payment_regime = fields.get("Régimen de pagos", "")
    status = fields.get("Estado", "")
    economic_activity = (
        fields.get("Actividad Económica")
        or fields.get("Actividad Economica")
        or ""
    )
    administration_local = (
        fields.get("Administración Local")
        or fields.get("Administracion Local")
        or ""
    )
    electronic_issuer = fields.get("Facturador Electrónico", "")
    vhm_licenses = fields.get("Licencias de Comercialización de VHM", "")

    comment_parts = []
    for label, val in [
        ("Nombre Comercial", commercial_name if commercial_name != name else None),
        ("Regimen de pagos", payment_regime),
        ("Estatus", status),
        ("Categoria", category),
        ("Actividad economica", economic_activity),
        ("Administracion local", administration_local),
        ("Facturador electronico", electronic_issuer),
    ]:
        if val:
            comment_parts.append(f"{label}: {val}")
    if vhm_licenses and vhm_licenses != "N/A":
        comment_parts.append(f"Licencias VHM: {vhm_licenses}")

    return {
        "rnc": actual_fiscal_id,
        "vat": actual_fiscal_id,
        "formatted_rnc": actual_fiscal_id,
        "name": name,
        "label": f"{actual_fiscal_id} - {name}" if actual_fiscal_id else name,
        "commercial_name": commercial_name,
        "status": status,
        "category": category,
        "payment_regime": payment_regime,
        "economic_activity": economic_activity,
        "administration_local": administration_local,
        "is_electronic_issuer": electronic_issuer.upper() == "SI",
        "comment": "; ".join(comment_parts),
        "company_type": "company" if len(actual_fiscal_id) == 9 else "person",
        "is_company": len(actual_fiscal_id) == 9,
        "source": "dgii_web",
    }


def parse_multiple_results(html_text):
    """Parse the multi-row grid returned by a name search. Returns list.

    The DGII grid table id is 'cphMain_gvBuscRazonSocial'.
    Columns: [0] Cédula/RNC, [1] Nombre/Razón Social, [2] Nombre Comercial,
              [3] Categoría, [4] Estado, [5] Facturador Electrónico.
    """
    results = []
    if not html_text:
        return results

    # Both the radgrid variant and the plain gridview variant
    _GRID_IDS = ('cphMain_gvBuscRazonSocial', 'cphMain_rgBusquedaNombre_ctl00')

    if _HAS_REQUESTS and BeautifulSoup:
        soup = BeautifulSoup(html_text, 'html.parser')
        grid = None
        for gid in _GRID_IDS:
            grid = soup.find('table', id=gid)
            if grid:
                break
        if not grid:
            return results

        tbody = grid.find('tbody') or grid
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
            rnc_raw = cells[0].text.strip()
            name = cells[1].text.strip()
            if not name:
                continue
            commercial_name = cells[2].text.strip() if len(cells) > 2 else name
            category = cells[3].text.strip() if len(cells) > 3 else ""
            status = cells[4].text.strip() if len(cells) > 4 else "ACTIVO"
            electronic_issuer = cells[5].text.strip() if len(cells) > 5 else ""
            actual_rnc = re.sub(r"[^0-9]", "", rnc_raw)
            results.append({
                "rnc": actual_rnc,
                "vat": actual_rnc,
                "name": name,
                "label": f"{actual_rnc} - {name}" if actual_rnc else name,
                "commercial_name": commercial_name or name,
                "status": status,
                "category": category,
                "is_electronic_issuer": electronic_issuer.upper() == "SI",
                "company_type": "company" if len(actual_rnc) == 9 else "person",
                "is_company": len(actual_rnc) == 9,
                "source": "dgii_web",
            })
    else:
        # Regex fallback — try both table IDs
        match_html = None
        for gid in _GRID_IDS:
            m2 = re.search(
                r'<table[^>]*id="%s"[^>]*>(.*?)</table>' % re.escape(gid),
                html_text, flags=re.IGNORECASE | re.DOTALL,
            )
            if m2:
                match_html = m2.group(1)
                break
        if not match_html:
            return results
        for r in re.findall(r'<tr[^>]*>(.*?)</tr>', match_html,
                            flags=re.IGNORECASE | re.DOTALL):
            cols = [_clean_html_text(c) for c in
                    re.findall(r'<td[^>]*>(.*?)</td>', r,
                               flags=re.IGNORECASE | re.DOTALL)]
            if len(cols) < 2 or not cols[1]:
                continue
            rnc = re.sub(r"[^0-9]", "", cols[0])
            name = cols[1]
            commercial_name = cols[2] if len(cols) > 2 else name
            category = cols[3] if len(cols) > 3 else ""
            status = cols[4] if len(cols) > 4 else "ACTIVO"
            electronic_issuer = cols[5] if len(cols) > 5 else ""
            results.append({
                "rnc": rnc,
                "vat": rnc,
                "name": name,
                "label": f"{rnc} - {name}" if rnc else name,
                "commercial_name": commercial_name or name,
                "status": status,
                "category": category,
                "is_electronic_issuer": electronic_issuer.upper() == "SI",
                "company_type": "company" if len(rnc) == 9 else "person",
                "is_company": len(rnc) == 9,
                "source": "dgii_web",
            })
    return results



# ─────────────────────────── public lookup API ───────────────────────────────

def lookup_rnc_cedula(fiscal_id, timeout=DEFAULT_TIMEOUT, lookup_url=DGII_RNC_LOOKUP_URL):
    """Look up a single RNC/Cédula. Returns dict or None (never raises)."""
    fiscal_id = normalize_fiscal_id(fiscal_id)
    if not fiscal_id:
        return None
    if not _HAS_REQUESTS:
        _logger.warning("lookup_rnc_cedula: 'requests' not available – skipping DGII query")
        return None

    try:
        session = _get_session()
        res = session.get(lookup_url, timeout=timeout)
        res.raise_for_status()
        form_state = extract_form_state(res.text)
        if not form_state:
            _logger.warning("lookup_rnc_cedula: no se pudieron extraer tokens del formulario DGII")
            return None

        payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "ctl00$cphMain$txtRNCCedula": fiscal_id,
            "ctl00$cphMain$btnBuscarPorRNC": "BUSCAR",
            "ctl00$cphMain$txtRazonSocial": "",
            "ctl00$cphMain$hidActiveTab": "rnc",
        }
        payload.update(form_state)

        res2 = session.post(lookup_url, data=payload, timeout=timeout)
        res2.raise_for_status()
        return parse_lookup_result(res2.text, fiscal_id)

    except Exception:
        # Non-blocking: log and return None so the UI doesn't crash
        _logger.warning(
            "lookup_rnc_cedula: fallo al consultar DGII para RNC=%s (no bloqueante)",
            fiscal_id, exc_info=True,
        )
        return None


def lookup_rnc_name(name, timeout=DEFAULT_TIMEOUT, lookup_url=DGII_RNC_LOOKUP_URL,
                    similarity_threshold=0.3, max_results=10):
    """
    Search DGII by name/razón-social.

    Returns a list sorted by similarity to `name`.
    If the DGII is unreachable or returns nothing the list is empty – never raises.
    """
    name = (name or "").strip()
    if len(name) < 3:
        return []
    if not _HAS_REQUESTS:
        _logger.warning("lookup_rnc_name: 'requests' not available – skipping DGII query")
        return []

    try:
        session = _get_session()
        res = session.get(lookup_url, timeout=timeout)
        res.raise_for_status()
        form_state = extract_form_state(res.text)
        if not form_state:
            return []

        payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "ctl00$cphMain$txtRNCCedula": "",
            "ctl00$cphMain$txtRazonSocial": name,
            "ctl00$cphMain$btnBuscarPorRazonSocial": "BUSCAR",
            "ctl00$cphMain$hidActiveTab": "nombre",
        }
        payload.update(form_state)

        res2 = session.post(lookup_url, data=payload, timeout=timeout)
        res2.raise_for_status()
        html2 = res2.text

        # Try to get a single exact-match contributor card first
        single = parse_lookup_result(html2)
        if single:
            return [single]

        # Otherwise parse the multi-result grid
        candidates = parse_multiple_results(html2)
        if not candidates:
            _logger.debug("lookup_rnc_name: no resultados en DGII para '%s' – omitiendo", name)
            return []

        # Sort by similarity and limit
        sorted_results = _sort_by_similarity(name, candidates,
                                              threshold=similarity_threshold)
        return sorted_results[:max_results]

    except Exception:
        # Non-blocking
        _logger.warning(
            "lookup_rnc_name: fallo al consultar DGII por nombre='%s' (no bloqueante)",
            name, exc_info=True,
        )
        return []


def fetch_json(url, params=None, timeout=DEFAULT_TIMEOUT):
    if not _HAS_REQUESTS:
        raise ImportError("'requests' not installed")
    res = requests.get(
        url, params=params,
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    res.raise_for_status()
    return res.json()


__all__ = [
    "DGII_RNC_LOOKUP_URL",
    "DEFAULT_TIMEOUT",
    "HTTPError",
    "URLError",
    "extract_form_state",
    "fetch_json",
    "lookup_rnc_cedula",
    "lookup_rnc_name",
    "normalize_fiscal_id",
    "parse_lookup_result",
]
