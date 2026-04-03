import json
import logging
import re

from odoo import http
from odoo.http import request
from odoo.addons.getupsoft_l10n_do_accounting.services.dgii_rnc_web import (
    lookup_rnc_cedula,
    lookup_rnc_name,
    normalize_fiscal_id,
    _sort_by_similarity,
)

_logger = logging.getLogger(__name__)


class Odoojs(http.Controller):

    # ── DGII (official source) ──────────────────────────────────────────────

    def _dgii_search(self, term):
        """
        Route the term to the appropriate DGII scraper.
        Always returns a list (possibly empty). Never raises.
        """
        fiscal_id = normalize_fiscal_id(term)
        if fiscal_id:
            # Numeric RNC or Cédula
            match = lookup_rnc_cedula(fiscal_id)
            return [match] if match else []
        elif len(term) >= 3:
            # Name search with built-in similarity sort inside lookup_rnc_name
            return lookup_rnc_name(term)
        return []

    # ── Local Odoo DB search ────────────────────────────────────────────────

    def _local_partner_search(self, term):
        """Search local res.partner records (ilike on name and vat)."""
        domain = ["|", ("name", "ilike", term), ("vat", "ilike", term)]
        partners = request.env["res.partner"].sudo().search(domain, limit=20)
        results = []
        for partner in partners:
            fiscal_id = re.sub(r"[^0-9]", "", partner.vat or "")
            name = (partner.name or "").strip()
            if not fiscal_id and not name:
                continue
            results.append({
                "rnc": fiscal_id,
                "vat": fiscal_id,
                "name": name,
                "label": "{} - {}".format(fiscal_id, name) if fiscal_id else name,
                "commercial_name": name,
                "status": "LOCAL",
                "category": "PARTNER",
                "comment": "Registro local Odoo.",
                "company_type": "company" if len(fiscal_id) == 9 else "person",
                "is_company": len(fiscal_id) == 9,
                "source": "odoo",
            })
        # Sort local results by similarity too so they appear in consistent order
        if results and not normalize_fiscal_id(term):
            results = _sort_by_similarity(term, results)
        return results

    # ── Merge and deduplicate ───────────────────────────────────────────────

    def _merge_results(self, *groups):
        """Merge multiple result groups, deduplicating by (vat, name)."""
        merged = []
        seen = set()
        for group in groups:
            for item in group:
                key = (
                    item.get("vat") or item.get("rnc") or "",
                    (item.get("name") or "").upper(),
                )
                if key in seen:
                    continue
                seen.add(key)
                merged.append(item)
        return merged

    # ── HTTP endpoint ───────────────────────────────────────────────────────

    @http.route("/dgii_ws", auth="public", cors="*")
    def index(self, **kwargs):
        term = (kwargs.get("term") or "").strip()
        if not term or len(term) < 2:
            return request.make_response(
                "[]", headers=[("Content-Type", "application/json")]
            )

        # DGII results come first (higher authority)
        dgii_results = self._dgii_search(term)
        local_results = self._local_partner_search(term)

        # If DGII returned nothing, local results still appear → non-blocking
        results = self._merge_results(dgii_results, local_results)

        return request.make_response(
            json.dumps(results),
            headers=[("Content-Type", "application/json")],
        )
