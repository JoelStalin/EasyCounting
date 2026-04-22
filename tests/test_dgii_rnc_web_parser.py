from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "integration"
    / "odoo"
    / "odoo19_getupsoft_do_localization"
    / "getupsoft_l10n_do_accounting"
    / "services"
    / "dgii_rnc_web.py"
)

spec = importlib.util.spec_from_file_location("dgii_rnc_web", MODULE_PATH)
dgii_rnc_web = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(dgii_rnc_web)


FORM_HTML = """
<form>
  <input type="hidden" name="__VIEWSTATE" value="viewstate-value" />
  <input type="hidden" name="__VIEWSTATEGENERATOR" value="generator-value" />
  <input type="hidden" name="__EVENTVALIDATION" value="eventvalidation-value" />
</form>
"""


FOUND_HTML = """
<span id="cphMain_lblInformacion" class="label text-info"></span>
<table id="cphMain_dvDatosContribuyentes">
  <tr><td>C&eacute;dula/RNC</td><td>225-0070642-3</td></tr>
  <tr><td>Nombre/Raz&oacute;n Social</td><td>JOEL STALIN MARTINEZ ESPINAL</td></tr>
  <tr><td>Nombre Comercial</td><td></td></tr>
  <tr><td>Categor&iacute;a</td><td></td></tr>
  <tr><td>R&eacute;gimen de pagos</td><td>RST</td></tr>
  <tr><td>Estado</td><td>ACTIVO</td></tr>
  <tr><td>Actividad Economica</td><td>DISE&Ntilde;O Y DESARROLLO DE SOFTWARE</td></tr>
  <tr><td>Administracion Local</td><td>ADM LOCAL ZONA ORIENTAL</td></tr>
  <tr><td>Facturador Electr&oacute;nico</td><td>NO</td></tr>
  <tr><td>Licencias de Comercializaci&oacute;n de VHM</td><td>N/A</td></tr>
</table>
"""


NOT_FOUND_HTML = """
<span id="cphMain_lblInformacion" class="label text-info">
  El RNC/Cédula consultado no se encuentra inscrito como Contribuyente.
</span>
<table id="cphMain_dvDatosContribuyentes"></table>
"""


def test_normalize_fiscal_id_accepts_plain_and_formatted_values():
    assert dgii_rnc_web.normalize_fiscal_id("22500706423") == "22500706423"
    assert dgii_rnc_web.normalize_fiscal_id("225-0070642-3") == "22500706423"
    assert dgii_rnc_web.normalize_fiscal_id("abc") == ""


def test_extract_form_state_reads_required_aspnet_fields():
    assert dgii_rnc_web.extract_form_state(FORM_HTML) == {
        "__VIEWSTATE": "viewstate-value",
        "__VIEWSTATEGENERATOR": "generator-value",
        "__EVENTVALIDATION": "eventvalidation-value",
    }


def test_parse_lookup_result_maps_dgii_partner_payload():
    payload = dgii_rnc_web.parse_lookup_result(FOUND_HTML, "22500706423")

    assert payload["vat"] == "22500706423"
    assert payload["formatted_rnc"] == "225-0070642-3"
    assert payload["name"] == "JOEL STALIN MARTINEZ ESPINAL"
    assert payload["payment_regime"] == "RST"
    assert payload["status"] == "ACTIVO"
    assert payload["economic_activity"] == "DISEÑO Y DESARROLLO DE SOFTWARE"
    assert payload["administration_local"] == "ADM LOCAL ZONA ORIENTAL"
    assert payload["source"] == "dgii_web"
    assert payload["company_type"] == "person"
    assert payload["is_company"] is False


def test_parse_lookup_result_returns_none_for_missing_contributor():
    assert dgii_rnc_web.parse_lookup_result(NOT_FOUND_HTML, "101010101") is None
