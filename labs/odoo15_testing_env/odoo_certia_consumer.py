# odoo_certia_consumer.py
# Ejecutar en Odoo Shell: docker exec -i <odoo_container> odoo shell ... < odoo_certia_consumer.py
"""
Certia -> Odoo JSON Consumer
Este script hace un GET al endpoint de Certia para traer los e-CF pendientes
de contabilizar y los inserta como account.move en Odoo.
"""
import requests
import json

CERTIA_API = "https://api.getupsoft.com.do"
CERTIA_TENANT_ID = 1  # ID del tenant principal en Certia

def consume_certia_ecf(env):
    print("=" * 60)
    print("  CERTIA -> ODOO JSON CONSUMER")
    print("=" * 60)

    try:
        resp = requests.get(
            f"{CERTIA_API}/api/v1/ecf/sync",
            params={"tenant_id": CERTIA_TENANT_ID},
            timeout=10
        )
        if resp.status_code != 200:
            print(f"[!] Error en Certia API: {resp.status_code} — {resp.text}")
            return

        ecf_list = resp.json().get("data", [])
        print(f"[*] Recibidos {len(ecf_list)} e-CF(s) para contabilizar desde Certia.")

    except Exception as e:
        print(f"[!] No se pudo conectar a Certia API: {e}")
        # Fallback: Usar datos mock para demo
        ecf_list = [
            {
                "ncf": "E3100000001",
                "doc_type": "31",
                "partner_vat": "130862346",
                "amount_total": 15000.0,
                "date": "2026-03-20",
                "track_id": "MOCK-TRK-E3100000001",
                "description": "Factura B2B generada por Certia API"
            },
            {
                "ncf": "E3200000001",
                "doc_type": "32",
                "partner_vat": "",
                "amount_total": 2500.0,
                "date": "2026-03-20",
                "track_id": "MOCK-TRK-E3200000001",
                "description": "Factura Consumo B2C generada por Certia API"
            },
            {
                "ncf": "E3300000001",
                "doc_type": "33",
                "partner_vat": "130862346",
                "amount_total": -1500.0,
                "date": "2026-03-20",
                "track_id": "MOCK-TRK-E3300000001",
                "description": "Nota de Crédito generada por Certia API"
            },
            {
                "ncf": "E3400000001",
                "doc_type": "34",
                "partner_vat": "130862346",
                "amount_total": 500.0,
                "date": "2026-03-20",
                "track_id": "MOCK-TRK-E3400000001",
                "description": "Nota de Débito generada por Certia API"
            },
            {
                "ncf": "E4100000001",
                "doc_type": "41",
                "partner_vat": "101027796",
                "amount_total": 8000.0,
                "date": "2026-03-20",
                "track_id": "MOCK-TRK-E4100000001",
                "description": "Factura de Compras generada por Certia API"
            },
        ]
        print(f"[*] Usando modo demo con {len(ecf_list)} e-CF(s) simulados.")

    # Mapa de tipos de e-CF -> tipo de asiento Odoo
    inv_type_map = {
        "31": "out_invoice",  # Crédito Fiscal → Factura Cliente
        "32": "out_invoice",  # Consumo → Factura Cliente
        "33": "out_refund",   # Nota Crédito → NC Cliente
        "34": "out_invoice",  # Nota Débito → ND Cliente
        "41": "in_invoice",   # Compras → Factura Proveedor
    }

    # Obtener diarios válidos
    sale_journal = env['account.journal'].search([
        ('type', '=', 'sale'), ('l10n_latam_use_documents', '=', True)
    ], limit=1)
    purchase_journal = env['account.journal'].search([
        ('type', '=', 'purchase'), ('l10n_latam_use_documents', '=', True)
    ], limit=1)

    # Cuenta de ingresos y gastos por defecto
    income_account = env['account.account'].search([('account_type', '=', 'income')], limit=1)
    expense_account = env['account.account'].search([('account_type', '=', 'expense')], limit=1)

    created = 0
    for ecf in ecf_list:
        doc_type = ecf.get("doc_type", "31")
        move_type = inv_type_map.get(doc_type, "out_invoice")

        # Buscar partner por VAT
        partner_vat = ecf.get("partner_vat", "")
        if partner_vat:
            partner = env['res.partner'].search([('vat', '=', partner_vat)], limit=1)
            if not partner:
                partner = env['res.partner'].search([], limit=1)
        else:
            partner = env['res.partner'].search([], limit=1)

        journal = purchase_journal if move_type == "in_invoice" else sale_journal
        if not journal:
            print(f"[!] No hay diario LATAM para tipo '{move_type}', saltando NCF {ecf['ncf']}")
            continue

        account = expense_account if move_type == "in_invoice" else income_account

        amount = abs(ecf.get("amount_total", 0.0))
        try:
            move = env['account.move'].create({
                'partner_id': partner.id if partner else False,
                'move_type': move_type,
                'journal_id': journal.id,
                'ref': ecf.get("ncf"),
                'narration': f"[Certia] NCF: {ecf['ncf']} | TrackID: {ecf.get('track_id')}",
                'invoice_line_ids': [(0, 0, {
                    'name': ecf.get("description", "Línea importada desde Certia"),
                    'quantity': 1,
                    'price_unit': amount,
                    'account_id': account.id if account else False,
                })],
            })
            move.action_post()
            print(f"[✓] {doc_type} — NCF: {ecf['ncf']} | Odoo ID: {move.id} | Asiento: {move.name}")
            created += 1
        except Exception as e:
            print(f"[X] Error al crear asiento para NCF {ecf['ncf']}: {e}")

    env.cr.commit()
    print("=" * 60)
    print(f"[*] TOTAL: {created}/{len(ecf_list)} e-CF(s) contabilizados en Odoo.")
    print("=" * 60)

consume_certia_ecf(env)
