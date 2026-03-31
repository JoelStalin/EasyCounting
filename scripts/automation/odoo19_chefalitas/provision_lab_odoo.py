import json
from datetime import date


company = env.company
do_country = env.ref("base.do")
company.country_id = do_country
company.partner_id.country_id = do_country
company.name = "Chefalitas Lab"
company.vat = "13199999999"
company.partner_id.name = company.name
company.partner_id.vat = company.vat

if not env["account.journal"].search_count([]):
    chart_code = env["account.chart.template"]._guess_chart_template(do_country)
    env["account.chart.template"].try_loading(chart_code, company)

sale_journal = env["account.journal"].search(
    [("type", "=", "sale"), ("company_id", "=", company.id)],
    limit=1,
)
if not sale_journal:
    raise RuntimeError("No se encontro diario de ventas tras cargar el plan contable.")

if not sale_journal.l10n_latam_use_documents:
    sale_journal.write({"l10n_latam_use_documents": True})

doc_type = env["l10n_latam.document.type"].search(
    [
        ("country_id", "=", do_country.id),
        ("doc_code_prefix", "=", "B01"),
    ],
    limit=1,
)
if not doc_type:
    raise RuntimeError("No se encontro el tipo documental B01.")

fiscal_position = env["account.fiscal.position"].search(
    [("name", "=", "Contribuyente Fiscal Demo")],
    limit=1,
)
fp_values = {
    "name": "Contribuyente Fiscal Demo",
    "l10n_do_ncf_type": "B11",
    "l10n_do_ncf_ids": [(6, 0, [doc_type.id])],
}
if fiscal_position:
    fiscal_position.write(fp_values)
else:
    fiscal_position = env["account.fiscal.position"].create(fp_values)

control = sale_journal.l10n_do_ncf_control_manager_ids.filtered(
    lambda item: item.l10n_latam_document_type_id == doc_type
)[:1]
if not control:
    control = env["ncf.control.manager"].create(
        {
            "journal_id": sale_journal.id,
            "l10n_latam_document_type_id": doc_type.id,
            "l10n_do_ncf_max_number": 99999999,
            "l10n_do_ncf_expiration_date": date(date.today().year, 12, 31),
        }
    )
else:
    control.write(
        {
            "l10n_do_ncf_max_number": max(control.l10n_do_ncf_max_number, 99999999),
            "l10n_do_ncf_expiration_date": date(date.today().year, 12, 31),
        }
    )

partner = env["res.partner"].search([("vat", "=", "101010101")], limit=1)
partner_values = {
    "name": "Cliente Prueba Odoo 19",
    "vat": "101010101",
    "country_id": do_country.id,
    "email": "cliente.prueba@example.com",
    "company_type": "company",
    "is_company": True,
    "property_account_position_id": fiscal_position.id,
}
if partner:
    partner.write(partner_values)
else:
    partner = env["res.partner"].create(partner_values)

product_tmpl = env["product.template"].search(
    [("default_code", "=", "LAB-SVC-001")],
    limit=1,
)
product_values = {
    "name": "Servicio Demo Odoo 19",
    "default_code": "LAB-SVC-001",
    "list_price": 2500.0,
    "type": "service",
}
if product_tmpl:
    product_tmpl.write(product_values)
else:
    product_tmpl = env["product.template"].create(product_values)
product = product_tmpl.product_variant_id

invoice = env["account.move"].create(
    {
        "move_type": "out_invoice",
        "partner_id": partner.id,
        "journal_id": sale_journal.id,
        "invoice_date": date.today(),
        "l10n_do_income_type": "01",
        "l10n_latam_document_type_id": doc_type.id,
        "invoice_line_ids": [
            (
                0,
                0,
                {
                    "product_id": product.id,
                    "name": "Servicio Demo Odoo 19",
                    "quantity": 1.0,
                    "price_unit": 2500.0,
                },
            )
        ],
    }
)
invoice.action_post()

report_period = date.today().strftime("%m/%Y")
dgii_report = env["dgii.reports"].search(
    [("name", "=", report_period), ("company_id", "=", company.id)],
    limit=1,
)
if not dgii_report:
    dgii_report = env["dgii.reports"].create(
        {"name": report_period, "company_id": company.id}
    )
dgii_report.generate_report()

env.cr.commit()

print(
    json.dumps(
        {
            "company": {
                "id": company.id,
                "name": company.name,
                "vat": company.vat,
                "chart_template": company.chart_template,
            },
            "saleJournal": {
                "id": sale_journal.id,
                "name": sale_journal.name,
                "useDocuments": sale_journal.l10n_latam_use_documents,
            },
            "ncfControl": {
                "id": control.id,
                "documentType": control.l10n_latam_document_type_id.doc_code_prefix,
                "maxNumber": control.l10n_do_ncf_max_number,
                "expirationDate": str(control.l10n_do_ncf_expiration_date),
            },
            "partner": {
                "id": partner.id,
                "name": partner.name,
                "vat": partner.vat,
                "fiscalPositionId": partner.property_account_position_id.id,
            },
            "product": {
                "id": product.id,
                "name": product.display_name,
                "defaultCode": product.default_code,
            },
            "invoice": {
                "id": invoice.id,
                "name": invoice.name,
                "state": invoice.state,
                "documentNumber": invoice.l10n_latam_document_number,
                "amountTotal": invoice.amount_total,
            },
            "dgiiReport": {
                "id": dgii_report.id,
                "name": dgii_report.name,
                "state": dgii_report.state,
                "saleRecords": dgii_report.sale_records,
                "purchaseRecords": dgii_report.purchase_records,
                "cancelRecords": dgii_report.cancel_records,
                "exteriorRecords": dgii_report.exterior_records,
            },
        },
        indent=2,
        ensure_ascii=True,
        default=str,
    )
)
