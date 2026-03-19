# No External Services For Odoo Integration

Fecha: `2026-03-18`

## Objetivo

Eliminar dependencias de servicios externos en la variante `getupsoft_do_localization` y sustituirlas por servicios internos del proyecto.

## Cambios

- se agrego el directorio local `app/services/local_rnc_directory.py`
- se expusieron rutas internas `GET /api/v1/odoo/rnc/search` y `GET /api/v1/odoo/rnc/{fiscal_id}`
- se creo el catalogo local `integration/odoo/getupsoft_do_localization/local_rnc_directory.json`
- el controlador Odoo `/dgii_ws` ahora consumira `dgii_encf` local o hara fallback a `res.partner`
- `res_partner.py` deja de usar SOAP DGII externo y pasa a consultar el servicio local o fallback Odoo

## Resultado

La integracion Odoo queda orientada a servicios internos del proyecto para autocomplete y validacion basica de RNC/Cedula.
