from __future__ import annotations

import json
import os
import time
import xmlrpc.client
from datetime import date


ODOO_URL = os.getenv("ODOO_URL", "http://127.0.0.1:19069")
ODOO_DB = os.getenv("ODOO_DB", "chefalitas19lab")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


def wait_for_odoo(timeout: int = 180) -> None:
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            version = common.version()
            if version:
                return
        except OSError:
            time.sleep(2)
            continue
        time.sleep(2)
    raise TimeoutError(f"Odoo no respondio en {ODOO_URL} dentro de {timeout}s")


def main() -> int:
    wait_for_odoo()
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        raise SystemExit("No fue posible autenticar contra Odoo.")

    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

    def execute(model: str, method: str, *args, **kwargs):
        return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, method, list(args), kwargs)

    company_ids = execute("res.company", "search", [], limit=1)
    if not company_ids:
        raise SystemExit("No se encontro compania inicial en el laboratorio Odoo.")
    company_id = company_ids[0]

    country_ids = execute("res.country", "search", [["code", "=", "DO"]], limit=1)
    if not country_ids:
        raise SystemExit("No se encontro el pais DO en el laboratorio Odoo.")
    do_country_id = country_ids[0]

    company_data = execute("res.company", "read", [company_id], ["partner_id", "currency_id"])[0]
    company_partner_id = company_data["partner_id"][0]

    execute(
        "res.partner",
        "write",
        [company_partner_id],
        {"name": "Chefalitas Lab", "vat": "13100000001", "country_id": do_country_id},
    )
    execute(
        "res.company",
        "write",
        [company_id],
        {"name": "Chefalitas Lab", "vat": "13100000001", "country_id": do_country_id},
    )

    journal_ids = execute("account.journal", "search", [["type", "=", "sale"], ["company_id", "=", company_id]], limit=1)
    if not journal_ids:
        raise SystemExit("No se encontro diario de ventas en el laboratorio Odoo.")
    journal_id = journal_ids[0]
    execute("account.journal", "write", [journal_id], {"l10n_latam_use_documents": True})

    control_ids = execute(
        "ncf.control.manager",
        "search_read",
        [["journal_id", "=", journal_id]],
        fields=["l10n_latam_document_type_id", "l10n_do_ncf_max_number", "l10n_do_ncf_expiration_date"],
        limit=20,
    )
    if not control_ids:
        raise SystemExit("El diario de ventas no genero controles NCF en el laboratorio.")

    doc_type_id = None
    for control in control_ids:
        document_type = control.get("l10n_latam_document_type_id") or []
        if document_type:
            doc_type_id = document_type[0]
            break
    if not doc_type_id:
        raise SystemExit("No fue posible seleccionar un tipo de documento fiscal para el diario.")

    partner_ids = execute("res.partner", "search", [["vat", "=", "101010101"]], limit=1)
    if partner_ids:
        partner_id = partner_ids[0]
    else:
        partner_id = execute(
            "res.partner",
            "create",
            [
                {
                    "name": "Cliente Prueba Odoo 19",
                    "vat": "101010101",
                    "country_id": do_country_id,
                    "email": "cliente.prueba@example.com",
                }
            ],
        )

    product_ids = execute("product.product", "search", [["default_code", "=", "LAB-SVC-001"]], limit=1)
    if product_ids:
        product_id = product_ids[0]
    else:
        product_id = execute(
            "product.product",
            "create",
            [
                {
                    "name": "Servicio Demo Odoo 19",
                    "default_code": "LAB-SVC-001",
                    "list_price": 2500.0,
                    "type": "service",
                }
            ],
        )

    invoice_vals = {
        "move_type": "out_invoice",
        "partner_id": partner_id,
        "journal_id": journal_id,
        "invoice_date": date.today().isoformat(),
        "invoice_line_ids": [
            (
                0,
                0,
                {
                    "product_id": product_id,
                    "name": "Servicio Demo Odoo 19",
                    "quantity": 1.0,
                    "price_unit": 2500.0,
                },
            )
        ],
        "l10n_do_income_type": "01",
    }
    if doc_type_id:
        invoice_vals["l10n_latam_document_type_id"] = doc_type_id

    invoice_id = execute("account.move", "create", [invoice_vals])
    execute("account.move", "action_post", [[invoice_id]])
    invoice_data = execute(
        "account.move",
        "read",
        [invoice_id],
        ["name", "state", "amount_total", "l10n_latam_document_number", "payment_state"],
    )[0]

    report_period = date.today().strftime("%m/%Y")
    report_ids = execute("dgii.reports", "search", [["name", "=", report_period], ["company_id", "=", company_id]], limit=1)
    report_id = report_ids[0] if report_ids else execute(
        "dgii.reports",
        "create",
        [{"name": report_period, "company_id": company_id}],
    )
    execute("dgii.reports", "generate_report", [[report_id]])
    report_data = execute(
        "dgii.reports",
        "read",
        [report_id],
        ["state", "sale_records", "purchase_records", "cancel_records", "exterior_records"],
    )[0]

    print(
        json.dumps(
            {
                "companyId": company_id,
                "partnerId": partner_id,
                "productId": product_id,
                "invoiceId": invoice_id,
                "invoice": invoice_data,
                "dgiiReportId": report_id,
                "dgiiReport": report_data,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
