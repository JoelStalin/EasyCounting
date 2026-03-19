# DGII Web RNC Autocomplete - 2026-03-18

## Cambio realizado

Se adapto `getupsoft_do_localization` para usar la consulta oficial de DGII por RNC/Cedula como fuente primaria de enriquecimiento de `res.partner` y de autocomplete Odoo.

## Archivos principales

- `integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting/services/dgii_rnc_web.py`
- `integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting/models/res_partner.py`
- `integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_rnc_search/controllers/controllers.py`
- `integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_rnc_search/README.md`
- `tests/test_dgii_rnc_web_parser.py`

## Comportamiento

- cuando el usuario introduce un RNC/Cedula completo, Odoo consulta primero:
  `https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/rnc.aspx`
- si DGII responde, se completa `vat`, `name`, `comment` y metadatos fiscales
- si DGII no responde o no encuentra datos, se hace fallback a `dgii_encf`
- si tampoco existe backend local, el autocomplete usa partners ya existentes en Odoo

## Verificacion

- `.\.venv\Scripts\python -m pytest tests\test_dgii_rnc_web_parser.py tests\test_odoo_local_directory.py -q`
  - resultado: `6 passed`
- `.\.venv\Scripts\python -m compileall ...`
  - resultado: `OK`
- prueba real del helper contra DGII:
  - entrada: `225-0070642-3`
  - salida: `JOEL STALIN MARTINEZ ESPINAL`, estado `ACTIVO`, regimen `RST`
