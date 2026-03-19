from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_odoo_rnc_lookup_reads_local_catalog() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/odoo/rnc/101010101")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rnc"] == "101010101"
    assert payload["source"] == "catalog"
    assert payload["name"] == "Empresa Fiscal Local SRL"


def test_odoo_rnc_search_can_merge_internal_tenants(monkeypatch) -> None:
    from app.services.local_rnc_directory import LocalRncDirectoryService

    def fake_load_tenants(self):
        return [
            {
                "rnc": "109876543",
                "vat": "109876543",
                "name": "Tenant Interno Uno",
                "label": "109876543 - Tenant Interno Uno",
                "commercial_name": "Tenant Interno Uno",
                "status": "ACTIVO",
                "category": "TENANT",
                "comment": "Registro interno sincronizado desde tenants.",
                "company_type": "company",
                "is_company": True,
                "source": "tenant",
            }
        ]

    monkeypatch.setattr(LocalRncDirectoryService, "_load_tenants", fake_load_tenants)

    client = TestClient(app)
    response = client.get("/api/v1/odoo/rnc/search", params={"term": "Tenant"})
    assert response.status_code == 200
    payload = response.json()
    assert any(item["rnc"] == "109876543" and item["source"] == "tenant" for item in payload)
