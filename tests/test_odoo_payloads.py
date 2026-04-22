import json
import sys

import httpx

API_URL = "http://127.0.0.1:28080/api/v1/odoo/invoices/transmit"
# The Local proxy routes /api/v1/ via nginx to the FastAPI container
# Let's also try direct access if nginx fails
API_URL_DIRECT = "http://127.0.0.1:8000/odoo/invoices/transmit"

def test_odoo_15_legacy_payload():
    """Simula una factura electrónica emitida desde el módulo l10n_do de Odoo 15."""
    print("--- Probando Payload de Odoo 15 ---")
    payload = {
        "odoo_invoice_id": 15001,
        "issue_date": "2026-03-19",
        "e_cf_type": "31",
        "currency": "DOP",
        "total_amount": 1180.00,
        "total_itbis": 180.00,
        "buyer": {
            "rnc": "101000000",
            "name": "Cliente VIP Legacy (Odoo 15)"
        },
        "lines": [
            {
                "product_name": "Consultoría Técnica (V15)",
                "quantity": 1.0,
                "unit_price": 1000.00,
                "itbis_rate": 18.0,
                "discount": 0.0
            }
        ]
    }
    
    try:
        response = httpx.post(API_URL_DIRECT, json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Respuesta Certia: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200, "Error en Odoo 15"
        print("✅ Odoo 15 Inbound Integración OK\n")
    except Exception as e:
        print(f"❌ Falló el request de Odoo 15: {e}\n")


def test_odoo_19_modern_payload():
    """Simula una factura electrónica B2C emitida desde el módulo l10n_do de Odoo 19 con POS."""
    print("--- Probando Payload de Odoo 19 ---")
    payload = {
        "odoo_invoice_id": 19045,
        "issue_date": "2026-03-19",
        "e_cf_type": "32", # Consumo (no exige buyer rnc por debajo del límite)
        "currency": "DOP",
        "total_amount": 550.00,
        "total_itbis": 0.00,
        "buyer": None, # Cliente final (Consumidor)
        "lines": [
            {
                "product_name": "Hamburguesa Chefalita",
                "quantity": 2.0,
                "unit_price": 275.00,
                "itbis_rate": 0.0,
                "discount": 0.0
            }
        ]
    }
    
    try:
        response = httpx.post(API_URL_DIRECT, json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Respuesta Certia: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200, "Error en Odoo 19"
        print("✅ Odoo 19 Inbound Integración OK\n")
    except Exception as e:
        print(f"❌ Falló el request de Odoo 19: {e}\n")


if __name__ == "__main__":
    test_odoo_15_legacy_payload()
    test_odoo_19_modern_payload()
