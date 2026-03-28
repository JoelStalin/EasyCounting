from __future__ import annotations

import json
import os
import subprocess
import time
import xmlrpc.client
from datetime import date, datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


ODOO_URL = os.getenv("ODOO_URL", "http://127.0.0.1:19069")
ODOO_DB = os.getenv("ODOO_DB", "odoo19e2e")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
ODOO_COMPANY_RNC = os.getenv("ODOO_COMPANY_RNC", "13199999999")
ODOO_COMPANY_NAME = os.getenv("ODOO_COMPANY_NAME", "EasyCounting Odoo Lab")

# Sales-side document types we want to exercise in Odoo.
TARGET_PREFIXES = [
    "B01",
    "B02",
    "B03",
    "B04",
    "E31",
    "E32",
    "E33",
    "E34",
    "E41",
    "E43",
    "E44",
    "E45",
    "E46",
    "E47",
]


def _as_id(value) -> int:
    if isinstance(value, (list, tuple)):
        if not value:
            raise RuntimeError("ID vacio en respuesta Odoo.")
        return int(value[0])
    return int(value)


def _connect_xmlrpc() -> tuple[xmlrpc.client.ServerProxy, int]:
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        raise RuntimeError("No fue posible autenticar en Odoo XML-RPC.")
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return models, int(uid)


def _execute(models: xmlrpc.client.ServerProxy, uid: int, model: str, method: str, *args, **kwargs):
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, method, list(args), kwargs)


def _setup_odoo(models: xmlrpc.client.ServerProxy, uid: int) -> dict[str, int]:
    country_ids = _execute(models, uid, "res.country", "search", [["code", "=", "DO"]], limit=1)
    if not country_ids:
        raise RuntimeError("No se encontro pais DO.")
    do_country_id = country_ids[0]
    fiscal_position_ids = _execute(models, uid, "account.fiscal.position", "search", [], limit=1)
    fiscal_position_id = _as_id(fiscal_position_ids) if fiscal_position_ids else None

    company_id = _as_id(_execute(models, uid, "res.company", "search", [], limit=1))
    company_data = _execute(models, uid, "res.company", "read", [company_id], ["partner_id"])[0]
    company_partner_id = company_data["partner_id"][0]

    _execute(
        models,
        uid,
        "res.company",
        "write",
        [company_id],
        {
            "name": ODOO_COMPANY_NAME,
            "vat": ODOO_COMPANY_RNC,
            "country_id": do_country_id,
            "l10n_do_ecf_issuer": True,
        },
    )
    _execute(
        models,
        uid,
        "res.partner",
        "write",
        [company_partner_id],
        {
            "name": ODOO_COMPANY_NAME,
            "vat": ODOO_COMPANY_RNC,
            "country_id": do_country_id,
            "company_type": "company",
            "is_company": True,
            **({"property_account_position_id": fiscal_position_id} if fiscal_position_id else {}),
        },
    )

    journal_id = _as_id(
        _execute(
        models,
        uid,
        "account.journal",
        "search",
        [["type", "=", "sale"], ["company_id", "=", company_id]],
        limit=1,
        )
    )
    try:
        _execute(models, uid, "account.journal", "write", [journal_id], {"l10n_latam_use_documents": True})
    except Exception:
        # When there are validated invoices, Odoo blocks changing this flag.
        pass

    partner_ids = _execute(models, uid, "res.partner", "search", [["vat", "=", "101010101"]], limit=1)
    if partner_ids:
        partner_id = _as_id(partner_ids)
        _execute(
            models,
            uid,
            "res.partner",
            "write",
            [partner_id],
            {
                "name": "Cliente Prueba DGII",
                "vat": "101010101",
                "country_id": do_country_id,
                "company_type": "company",
                "is_company": True,
                "email": "cliente.prueba@example.com",
                **({"property_account_position_id": fiscal_position_id} if fiscal_position_id else {}),
            },
        )
    else:
        fallback_partner_ids = _execute(models, uid, "res.partner", "search", [], limit=1)
        if not fallback_partner_ids:
            raise RuntimeError("No existe ningun partner base para reutilizar.")
        partner_id = _as_id(fallback_partner_ids)
        _execute(
            models,
            uid,
            "res.partner",
            "write",
            [partner_id],
            {
                "name": "Cliente Prueba DGII",
                "vat": "101010101",
                "country_id": do_country_id,
                "company_type": "company",
                "is_company": True,
                "email": "cliente.prueba@example.com",
                **({"property_account_position_id": fiscal_position_id} if fiscal_position_id else {}),
            },
        )

    product_ids = _execute(models, uid, "product.product", "search", [["default_code", "=", "LAB-SVC-001"]], limit=1)
    if product_ids:
        product_id = _as_id(product_ids)
    else:
        product_id = _as_id(
            _execute(
            models,
            uid,
            "product.product",
            "create",
            [
                {
                    "name": "Servicio Prueba DGII",
                    "default_code": "LAB-SVC-001",
                    "list_price": 1500.0,
                    "type": "service",
                }
            ],
            )
        )

    doc_types = _execute(
        models,
        uid,
        "l10n_latam.document.type",
        "search_read",
        [["doc_code_prefix", "in", TARGET_PREFIXES]],
        fields=["id", "name", "doc_code_prefix", "internal_type"],
        limit=300,
    )
    by_prefix = {row["doc_code_prefix"]: row for row in doc_types}

    # Ensure control manager sequence exists for each doc type.
    for prefix in TARGET_PREFIXES:
        row = by_prefix.get(prefix)
        if not row:
            continue
        control_ids = _execute(
            models,
            uid,
            "ncf.control.manager",
            "search",
            [["journal_id", "=", journal_id], ["l10n_latam_document_type_id", "=", row["id"]]],
            limit=1,
        )
        if control_ids:
            _execute(
                models,
                uid,
                "ncf.control.manager",
                "write",
                control_ids,
                {
                    "l10n_do_ncf_max_number": 99999999,
                    "l10n_do_ncf_expiration_date": date(date.today().year, 12, 31).isoformat(),
                },
            )
        else:
            _execute(
                models,
                uid,
                "ncf.control.manager",
                "create",
                [
                    {
                        "journal_id": journal_id,
                        "l10n_latam_document_type_id": row["id"],
                        "l10n_do_ncf_max_number": 99999999,
                        "l10n_do_ncf_expiration_date": date(date.today().year, 12, 31).isoformat(),
                    }
                ],
            )

    return {
        "company_id": company_id,
        "journal_id": journal_id,
        "partner_id": partner_id,
        "product_id": product_id,
    }


def _create_and_post_matrix(models: xmlrpc.client.ServerProxy, uid: int, setup: dict[str, int]) -> dict:
    doc_types = _execute(
        models,
        uid,
        "l10n_latam.document.type",
        "search_read",
        [["doc_code_prefix", "in", TARGET_PREFIXES]],
        fields=["id", "name", "doc_code_prefix", "internal_type"],
        limit=300,
    )
    by_prefix = {row["doc_code_prefix"]: row for row in doc_types}

    results: list[dict] = []
    base_invoice_id = None

    for idx, prefix in enumerate(TARGET_PREFIXES, start=1):
        row = by_prefix.get(prefix)
        if not row:
            results.append({"prefix": prefix, "status": "SKIPPED", "error": "Tipo documental no encontrado"})
            continue

        move_type = "out_refund" if row.get("internal_type") == "credit_note" else "out_invoice"
        vals = {
            "move_type": move_type,
            "partner_id": setup["partner_id"],
            "journal_id": setup["journal_id"],
            "invoice_date": date.today().isoformat(),
            "l10n_latam_document_type_id": row["id"],
            "l10n_do_income_type": "01",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": setup["product_id"],
                        "name": f"Servicio prueba {prefix}",
                        "quantity": 1.0,
                        "price_unit": 1000.0 + idx,
                    },
                )
            ],
        }
        if move_type == "out_refund" and base_invoice_id:
            vals["reversed_entry_id"] = base_invoice_id

        try:
            invoice_id = _as_id(_execute(models, uid, "account.move", "create", [vals]))
            _execute(models, uid, "account.move", "action_post", invoice_id)
            invoice_data = _execute(
                models,
                uid,
                "account.move",
                "read",
                [invoice_id],
                [
                    "name",
                    "state",
                    "move_type",
                    "l10n_latam_document_number",
                    "l10n_latam_document_type_id",
                    "amount_total",
                ],
            )[0]

            if prefix in {"B01", "E31"} and base_invoice_id is None:
                base_invoice_id = invoice_id

            results.append(
                {
                    "prefix": prefix,
                    "status": "POSTED",
                    "invoice_id": invoice_id,
                    "invoice": invoice_data,
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append({"prefix": prefix, "status": "FAILED", "error": str(exc)})

    return {"results": results}


def _capture_ui_evidence(artifacts_dir: Path, posted_invoices: list[dict]) -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    # Headless keeps the run deterministic in CI/local shells.
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    try:
        login_url = f"{ODOO_URL}/web/login?db={ODOO_DB}"
        driver.get(login_url)
        login_input = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='login']:not([type='hidden'])"))
        )
        password_input = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='password']:not([type='hidden'])"))
        )
        login_input.clear()
        login_input.send_keys(ODOO_USER)
        password_input.clear()
        password_input.send_keys(ODOO_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1.5)
        driver.save_screenshot(str(artifacts_dir / "01_odoo_home.png"))

        driver.get(f"{ODOO_URL}/web#model=account.move&view_type=list")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1.5)
        driver.save_screenshot(str(artifacts_dir / "02_odoo_invoice_list.png"))

        shot_idx = 3
        for item in posted_invoices:
            invoice_id = item.get("invoice_id")
            prefix = item.get("prefix", "NA")
            if not invoice_id:
                continue
            driver.get(f"{ODOO_URL}/web#id={invoice_id}&model=account.move&view_type=form")
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1.0)
            driver.save_screenshot(str(artifacts_dir / f"{shot_idx:02d}_invoice_{prefix}_{invoice_id}.png"))
            shot_idx += 1
    finally:
        driver.quit()


def _collect_integration_logs(artifacts_dir: Path) -> None:
    nginx_cmd = ["docker", "logs", "dgii_encf-nginx-1", "--since", "20m"]
    web_cmd = ["docker", "logs", "dgii_encf-web-1", "--since", "20m"]
    odoo_cmd = ["docker", "logs", "odoo19e2e-web", "--since", "20m"]

    nginx_out = subprocess.run(nginx_cmd, capture_output=True, text=True, check=False).stdout
    web_out = subprocess.run(web_cmd, capture_output=True, text=True, check=False).stdout
    odoo_out = subprocess.run(odoo_cmd, capture_output=True, text=True, check=False).stdout

    (artifacts_dir / "nginx_last20m.log").write_text(nginx_out, encoding="utf-8")
    (artifacts_dir / "hub_last20m.log").write_text(web_out, encoding="utf-8")
    (artifacts_dir / "odoo_last20m.log").write_text(odoo_out, encoding="utf-8")

    # Focused integration summary.
    interesting = []
    for line in nginx_out.splitlines():
        if "/api/v1/odoo/invoices/transmit" in line:
            interesting.append(line)
    (artifacts_dir / "odoo_to_hub_requests.log").write_text("\n".join(interesting), encoding="utf-8")


def main() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifacts_dir = Path(f"docs/evidence/odoo_matrix_{ts}")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    models, uid = _connect_xmlrpc()
    setup = _setup_odoo(models, uid)
    matrix = _create_and_post_matrix(models, uid, setup)
    (artifacts_dir / "matrix_results.json").write_text(json.dumps(matrix, indent=2, ensure_ascii=False), encoding="utf-8")

    posted = [item for item in matrix["results"] if item.get("status") == "POSTED"]
    _capture_ui_evidence(artifacts_dir, posted)
    _collect_integration_logs(artifacts_dir)

    summary = {
        "artifacts_dir": str(artifacts_dir),
        "posted_count": len(posted),
        "failed_count": len([x for x in matrix["results"] if x.get("status") == "FAILED"]),
        "skipped_count": len([x for x in matrix["results"] if x.get("status") == "SKIPPED"]),
    }
    (artifacts_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    fiscal_position_ids = _execute(models, uid, "account.fiscal.position", "search", [], limit=1)
    fiscal_position_id = _as_id(fiscal_position_ids) if fiscal_position_ids else None
