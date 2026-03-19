# getupsoft_l10n_do_rnc_search

Modulo de busqueda de RNC DGII adaptado por GetUpSoft para la suite `getupsoft_do_localization`.

Objetivo:

- autocompletar partners Odoo con datos consultados por RNC o cedula
- complementar el flujo fiscal dominicano usado junto a `getupsoft_l10n_do_accounting`
- servir como punto de apoyo para la futura sincronizacion con `dgii_encf`

Notas:

- esta copia forma parte del refactor local realizado sobre el snapshot importado desde `jabiya`
- el branding, manifests y assets fueron ajustados para dejar nombres tecnicos consistentes con `getupsoft_*`
- no usa DGII SOAP ni servicios publicos de terceros para autocomplete
- el enriquecimiento exacto por RNC/Cedula usa la consulta oficial DGII:
  `https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/rnc.aspx`
- el controlador Odoo `/dgii_ws` intenta primero la consulta oficial cuando recibe un RNC/Cedula completo
- si DGII no responde o no encuentra datos, el flujo hace fallback al backend local `dgii_encf` via `GET /api/v1/odoo/rnc/search`
- si tampoco hay backend local, el autocomplete cae al partner local de Odoo
- el parametro Odoo `getupsoft_dgii_encf.base_url` define la URL base del backend local opcional
