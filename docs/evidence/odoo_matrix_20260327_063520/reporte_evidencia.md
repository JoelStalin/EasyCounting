# Evidencia Odoo -> Hub (corrida 2026-03-27 06:35)

## Resumen
- posted_count: 14
- failed_count: 0
- Flujo validado: Odoo crea factura -> modulo `odoo19_getupsoft_do_localization` transmite -> hub responde `202 Accepted`.

## Facturas por tipo
- B01 -> invoice_id 171 -> B01 00000069
- B02 -> invoice_id 172 -> B01 00000070
- B03 -> invoice_id 173 -> B01 00000071
- B04 -> invoice_id 174 -> B01 00000072
- E31 -> invoice_id 175 -> B01 00000073
- E32 -> invoice_id 176 -> B01 00000074
- E33 -> invoice_id 177 -> B01 00000075
- E34 -> invoice_id 178 -> B01 00000076
- E41 -> invoice_id 179 -> B01 00000077
- E43 -> invoice_id 180 -> B01 00000078
- E44 -> invoice_id 181 -> B01 00000079
- E45 -> invoice_id 182 -> B01 00000080
- E46 -> invoice_id 183 -> B01 00000081
- E47 -> invoice_id 184 -> B01 00000082

## Evidencia
- PDF consolidado: `docs/evidence/odoo_facturas_evidencia_20260327_063704.pdf`
- Carpeta corrida: `docs/evidence/odoo_matrix_20260327_063520`
- PDFs por tipo: `docs/evidence/odoo_matrix_20260327_063520/pdf_por_comprobante`
- Log Odoo (solo exitos): `docs/evidence/odoo_matrix_20260327_063520/odoo_transmit_success_only.log`
- Log Hub (solo 202): `docs/evidence/odoo_matrix_20260327_063520/hub_transmit_202_only.log`

## Nota
- Los nombres visibles en Odoo aparecen con prefijo `B01` en esta configuración del módulo, aunque el tipo documental aplicado en la matriz sí corresponde al prefijo objetivo.
