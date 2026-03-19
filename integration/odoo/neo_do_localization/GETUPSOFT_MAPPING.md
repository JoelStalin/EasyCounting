# GetUpSoft Mapping

Este documento resume como encaja `neo_do_localization` con el modelo actual de `dgii_encf`.

## Dominio Odoo -> dominio dgii_encf

- `res.company`
  - equivalente local: `app/models/tenant.py`
  - campos locales relevantes:
    - `name`
    - `rnc`
    - `env`
    - `dgii_base_ecf`
    - `dgii_base_fc`
    - `cert_ref`
    - `p12_kms_key`

- `account.move`
  - equivalente local: `app/models/invoice.py`
  - campos locales relevantes:
    - `tenant_id`
    - `encf`
    - `tipo_ecf`
    - `rnc_receptor`
    - `xml_path`
    - `xml_hash`
    - `estado_dgii`
    - `track_id`
    - `codigo_seguridad`
    - `total`
    - `fecha_emision`
    - `contabilizado`
    - `accounted_at`
    - `asiento_referencia`

- busqueda RNC DGII
  - addon Odoo: `l10n_do_rnc_search`
  - equivalente funcional local: validacion de emisor/receptor y futura resolucion de partners para sincronizacion Odoo

## Modulos mas alineados con este repo

- `l10n_do_accounting`
  - relevante para documentos fiscales, posiciones fiscales y comportamiento contable
- `l10n_do_e_accounting`
  - relevante para el flag de emisor electronico y comportamiento e-CF en `account.move`
- `l10n_do_rnc_search`
  - relevante para validar y enriquecer partners por RNC

## Flujo recomendado de integracion

1. `dgii_encf` emite y persiste un `Invoice`.
2. El futuro servicio `odoo_integration` traduce `Invoice` -> payload Odoo `account.move`.
3. `Tenant` se resuelve contra `res.company` usando `rnc` como identificador primario.
4. `neo_do_localization` aporta la semantica fiscal dominicana dentro de Odoo para que el documento quede alineado con el contexto local.
5. El estado de contabilizacion Odoo puede regresar a `dgii_encf` para poblar `contabilizado`, `accounted_at` y `asiento_referencia`.

## Brechas actuales

- Este repositorio todavia no implementa el microservicio `odoo_integration`.
- No existe aun un cliente JSON-RPC ni webhook Odoo dentro de `app/`.
- El snapshot copiado es Odoo 15, mientras que la arquitectura documentada menciona Odoo 18; eso requiere validacion antes de produccion.
