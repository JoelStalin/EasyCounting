import json
import logging

from odoo import http
from odoo.http import request
from odoo.addons.getupsoft_l10n_do_accounting.services.dgii_rnc_web import (
    HTTPError,
    URLError,
    fetch_json,
    lookup_rnc_cedula,
    normalize_fiscal_id,
)

_logger = logging.getLogger(__name__)


class Odoojs(http.Controller):
    def _service_base_url(self):
        base_url = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("getupsoft_dgii_encf.base_url", default="")
            .strip()
        )
        return base_url.rstrip("/")

    def _official_partner_search(self, term):
        fiscal_id = normalize_fiscal_id(term)
        if not fiscal_id:
            return []

        try:
            match = lookup_rnc_cedula(fiscal_id)
            return [match] if match else []
        except (HTTPError, URLError, ValueError):
            _logger.warning(
                "Fallo autocomplete oficial DGII para term=%s",
                term,
                exc_info=True,
            )
            return []

    def _proxy_local_search(self, term):
        base_url = self._service_base_url()
        if not base_url:
            return []

        try:
            payload = fetch_json(
                "{}/api/v1/odoo/rnc/search".format(base_url),
                params={"term": term, "limit": 20},
                timeout=5,
            )
            return payload if isinstance(payload, list) else []
        except (HTTPError, URLError, ValueError):
            _logger.warning("Fallo proxy local RNC para term=%s", term, exc_info=True)
            return []

    def _local_partner_search(self, term):
        domain = ["|", ("name", "ilike", term), ("vat", "ilike", term)]
        partners = request.env["res.partner"].sudo().search(domain, limit=20)
        results = []
        for partner in partners:
            fiscal_id = "".join(char for char in (partner.vat or "") if char.isdigit())
            name = (partner.name or "").strip()
            if not fiscal_id and not name:
                continue
            results.append(
                {
                    "rnc": fiscal_id,
                    "vat": fiscal_id,
                    "name": name,
                    "label": "{} - {}".format(fiscal_id or "N/A", name),
                    "commercial_name": name,
                    "status": "LOCAL",
                    "category": "PARTNER",
                    "comment": "Registro local Odoo.",
                    "company_type": "company" if len(fiscal_id) == 9 else "person",
                    "is_company": len(fiscal_id) == 9,
                    "source": "odoo",
                }
            )
        return results

    def _merge_results(self, *groups):
        merged = []
        seen = set()
        for group in groups:
            for item in group:
                key = (
                    item.get("vat") or item.get("rnc") or "",
                    item.get("name") or "",
                )
                if key in seen:
                    continue
                seen.add(key)
                merged.append(item)
        return merged

    @http.route("/dgii_ws", auth="public", cors="*")
    def index(self, **kwargs):
        term = (kwargs.get("term") or "").strip()
        if not term:
            return request.make_response("[]", headers=[("Content-Type", "application/json")])

        results = self._merge_results(
            self._official_partner_search(term),
            self._proxy_local_search(term),
            self._local_partner_search(term),
        )

        return request.make_response(
            json.dumps(results),
            headers=[("Content-Type", "application/json")],
        )
