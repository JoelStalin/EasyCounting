# GetUpSoft Mapping

Este documento resume como encaja `getupsoft_do_localization` con el modelo actual de `dgii_encf`.

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
  - addon Odoo: `getupsoft_l10n_do_rnc_search`
  - equivalente funcional local: validacion de emisor/receptor y futura resolucion de partners para sincronizacion Odoo

## Modulos mas alineados con este repo

- `getupsoft_l10n_do_accounting`
  - relevante para documentos fiscales, posiciones fiscales y comportamiento contable
- `getupsoft_l10n_do_e_accounting`
  - relevante para el flag de emisor electronico y comportamiento e-CF en `account.move`
- `getupsoft_l10n_do_rnc_search`
  - relevante para validar y enriquecer partners por RNC

## Flujo recomendado de integracion

1. `dgii_encf` emite y persiste un `Invoice`.
2. El futuro servicio `odoo_integration` traduce `Invoice` -> payload Odoo `account.move`.
3. `Tenant` se resuelve contra `res.company` usando `rnc` como identificador primario.
4. `getupsoft_do_localization` aporta la semantica fiscal dominicana dentro de Odoo para que el documento quede alineado con el contexto local.
5. El estado de contabilizacion Odoo puede regresar a `dgii_encf` para poblar `contabilizado`, `accounted_at` y `asiento_referencia`.

## Superficie actual del backend

- El backend expone `admin_router` y `cliente_router` bajo `/api` y `/api/v1`.
- La persistencia relevante para una futura sincronizacion ya existe en `Tenant`, `Invoice`, `TenantSettings` e `InvoiceLedgerEntry`.
- Se agrego un directorio local para Odoo en `GET /api/v1/odoo/rnc/search` y `GET /api/v1/odoo/rnc/{fiscal_id}`.
- Las rutas de billing viven en `app/billing/routes.py`, pero hoy no estan montadas en `app/main.py`; cualquier puente Odoo debe apoyarse en servicios internos o en nuevos endpoints dedicados.

## Brechas actuales

- Este repositorio todavia no implementa el microservicio `odoo_integration`.
- No existe aun un cliente JSON-RPC ni webhook Odoo dentro de `app/`.
- El snapshot remoto de origen era Odoo 15; esta variante local fue elevada a `Odoo 19.0`, pero el modulo `getupsoft_l10n_do_pos` queda pendiente de reescritura OWL para compatibilidad funcional real.
