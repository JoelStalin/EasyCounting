# -*- coding: utf-8 -*-
"""Official DGII RNC/Cedula lookup helpers for Odoo localization."""

from __future__ import annotations

import json
import re
from html import unescape
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

DGII_RNC_LOOKUP_URL = (
    "https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/rnc.aspx"
)

DEFAULT_TIMEOUT = 10

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

_JSON_HEADERS = {
    "Accept": "application/json",
}

_FORM_FIELD_NAMES = (
    "__VIEWSTATE",
    "__VIEWSTATEGENERATOR",
    "__EVENTVALIDATION",
)


def normalize_fiscal_id(value):
    digits = re.sub(r"[^0-9]", "", value or "")
    return digits if len(digits) in (9, 11) else ""


def extract_form_state(html_text):
    state = {}
    for field_name in _FORM_FIELD_NAMES:
        match = re.search(
            r'name="%s"[^>]*value="([^"]*)"' % re.escape(field_name),
            html_text,
            flags=re.IGNORECASE,
        )
        if not match:
            return {}
        state[field_name] = unescape(match.group(1))
    return state


def parse_lookup_result(html_text, fiscal_id):
    message = _extract_info_message(html_text)
    if message and "no se encuentra inscrito" in message.lower():
        return None

    table_match = re.search(
        r'<table[^>]*id="cphMain_dvDatosContribuyentes"[^>]*>(.*?)</table>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not table_match:
        return None

    cells = [
        _clean_html_text(cell)
        for cell in re.findall(
            r"<td[^>]*>(.*?)</td>",
            table_match.group(1),
            flags=re.IGNORECASE | re.DOTALL,
        )
    ]
    if len(cells) < 4:
        return None

    fields = {}
    for index in range(0, len(cells) - 1, 2):
        key = (cells[index] or "").rstrip(":").strip()
        if not key:
            continue
        fields[key] = cells[index + 1].strip()

    name = fields.get("Nombre/Razón Social", "")
    if not name:
        return None

    formatted_rnc = fields.get("Cédula/RNC") or fiscal_id
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
    if commercial_name and commercial_name != name:
        comment_parts.append("Nombre Comercial: %s" % commercial_name)
    if payment_regime:
        comment_parts.append("Regimen de pagos: %s" % payment_regime)
    if status:
        comment_parts.append("Estatus: %s" % status)
    if category:
        comment_parts.append("Categoria: %s" % category)
    if economic_activity:
        comment_parts.append("Actividad economica: %s" % economic_activity)
    if administration_local:
        comment_parts.append("Administracion local: %s" % administration_local)
    if electronic_issuer:
        comment_parts.append("Facturador electronico: %s" % electronic_issuer)
    if vhm_licenses and vhm_licenses != "N/A":
        comment_parts.append("Licencias VHM: %s" % vhm_licenses)

    return {
        "rnc": fiscal_id,
        "vat": fiscal_id,
        "formatted_rnc": formatted_rnc,
        "name": name,
        "label": "%s - %s" % (formatted_rnc, name),
        "commercial_name": commercial_name,
        "status": status,
        "category": category,
        "payment_regime": payment_regime,
        "economic_activity": economic_activity,
        "administration_local": administration_local,
        "is_electronic_issuer": electronic_issuer.upper() == "SI",
        "comment": "; ".join(comment_parts),
        "company_type": "company" if len(fiscal_id) == 9 else "person",
        "is_company": len(fiscal_id) == 9,
        "source": "dgii_web",
    }


def lookup_rnc_cedula(fiscal_id, timeout=DEFAULT_TIMEOUT, lookup_url=DGII_RNC_LOOKUP_URL):
    fiscal_id = normalize_fiscal_id(fiscal_id)
    if not fiscal_id:
        return None

    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    form_html = _http_open_text(opener, lookup_url, timeout=timeout)
    form_state = extract_form_state(form_html)
    if not form_state:
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

    response_html = _http_open_text(
        opener,
        lookup_url,
        data=urlencode(payload).encode("utf-8"),
        timeout=timeout,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
    )
    return parse_lookup_result(response_html, fiscal_id)


def fetch_json(url, params=None, timeout=DEFAULT_TIMEOUT):
    if params:
        url = "%s?%s" % (url, urlencode(params))
    opener = build_opener()
    payload = _http_open_text(opener, url, timeout=timeout, headers=_JSON_HEADERS)
    return json.loads(payload)


def _http_open_text(opener, url, data=None, timeout=DEFAULT_TIMEOUT, headers=None):
    request_headers = dict(_BROWSER_HEADERS)
    if headers:
        request_headers.update(headers)

    request = Request(url, data=data, headers=request_headers)
    with opener.open(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, "replace")


def _extract_info_message(html_text):
    match = re.search(
        r'<span[^>]*id="cphMain_lblInformacion"[^>]*>(.*?)</span>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    return _clean_html_text(match.group(1))


def _clean_html_text(fragment):
    fragment = re.sub(r"<br\s*/?>", " | ", fragment, flags=re.IGNORECASE)
    fragment = re.sub(r"&nbsp;", " ", fragment, flags=re.IGNORECASE)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", unescape(fragment)).strip()


__all__ = [
    "DGII_RNC_LOOKUP_URL",
    "DEFAULT_TIMEOUT",
    "HTTPError",
    "URLError",
    "extract_form_state",
    "fetch_json",
    "lookup_rnc_cedula",
    "normalize_fiscal_id",
    "parse_lookup_result",
]
