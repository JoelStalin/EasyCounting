# Coverage Matrix Comprobantes

## Fuente funcional

- `integration/odoo/odoo19_getupsoft_do_localization/getupsoft_l10n_do_e_accounting/data/l10n_latam.document.type.csv`
- corrida controlada local: `tests/artifacts/2026-03-25_23-50-25_controlled_local_matrix/run-summary.json`

| Tipo | Clasificación | Odoo localización | EasyCounting backend | DGII oficial en entorno auditado | 0.001 local | Resultado local |
| --- | --- | --- | --- | --- | --- | --- |
| E31 | e-fiscal | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E32 | e-consumer | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E33 | e-debit_note | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E34 | e-credit_note | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E41 | e-informal | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E43 | e-minor | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E44 | e-special | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E45 | e-governmental | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E46 | e-export | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |
| E47 | e-exterior | soportado | soportado | bloqueado por gate externo | sí | PASS_LOCAL |

## Restricción registrada

El sandbox oficial DGII no fue ejecutado porque el entorno auditado no disponía de certificado real ni credenciales externas activas. La matriz oficial queda lista para completarse en `TEST/CERT` usando el mismo pipeline y artefactos.
