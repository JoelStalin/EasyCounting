# dgii_test_set_runner.py
import sys

def run_dgii_test_set(env):
    print("=========================================================")
    print("  INICIANDO EMISIÓN DE SET DE PRUEBAS (PRE-CERT DGII)  ")
    print("=========================================================")
    
    # 1. Preparar Partners de Prueba
    b2b_partner = env['res.partner'].search([('vat', '!=', False)], limit=1)
    if not b2b_partner:
        print("[!] No hay clientes B2B (con RNC) configurados en BD. Favor crear al menos uno.")
        return

    b2c_partner = env['res.partner'].search([('vat', '=', False), ('customer_rank', '>', 0)], limit=1)
    if not b2c_partner:
        b2c_partner = env['res.partner'].search([('vat', '=', False)], limit=1)
        if not b2c_partner:
            print("[!] No hay clientes B2C (Consumidor Final) en BD.")
            return
        
    # Obtener diarios aptos para e-CF
    sale_journal = env['account.journal'].search([('type', '=', 'sale'), ('l10n_latam_use_documents', '=', True)], limit=1)
    if not sale_journal:
        print("[!] ATENCIÓN: No hay diarios de venta configurados para usar documentos LATAM.")
        return

    def emit_ecf(doc_type_name, partner, amount, inv_type='out_invoice', log_name=""):
        doc_type = env['l10n_latam.document.type'].search([('name', 'ilike', doc_type_name)], limit=1)
        if not doc_type:
            print(f"[!] Tipo de Documento no encontrado para: {doc_type_name}")
            return None
            
        move_vals = {
            'partner_id': partner.id,
            'move_type': inv_type,
            'journal_id': sale_journal.id,
            'l10n_do_expense_type': '02',  # DGII expense type at move level
            'l10n_latam_document_type_id': doc_type.id,
            'invoice_line_ids': [(0, 0, {
                'name': f'Prueba e-CF Caso: {log_name}',
                'quantity': 1,
                'price_unit': amount,
            })]
        }
        
        move = env['account.move'].create(move_vals)
        move.action_post()
        print(f"[*] e-CF {doc_type_code} Emitido ({log_name}): {move.name} | Estado: {move.state}")
        return move

    try:
        # Caso 1: E-CF 31 - Crédito Fiscal (B2B)
        ecf_31 = emit_ecf('Crédito Fiscal Electrónica', b2b_partner, 15000.0, log_name="B2B Comercial")
        
        # Caso 2: E-CF 32 - Consumo (B2C)
        ecf_32 = emit_ecf('Consumo Electrónica', b2c_partner, 2500.0, log_name="B2C Cliente Final")
        
        if ecf_31:
            # Caso 3: E-CF 33 - Nota de Crédito (Reversión parcial/total de E-CF 31)
            wizard = env['account.move.reversal'].with_context(active_model="account.move", active_ids=ecf_31.ids).create({
                'reason': 'Devolución de mercancía - Prueba DGII',
                'refund_method': 'refund',
                'journal_id': ecf_31.journal_id.id,
            })
            res = wizard.reverse_moves()
            if res and 'res_id' in res:
                nc_move = env['account.move'].browse(res['res_id'])
                nc_move.action_post()
                print(f"[*] e-CF 33 Emitido (Nota Crédito): {nc_move.name} | Reversión de: {ecf_31.name}")

        # Omitimos Casos complejos como 34 (Nota de Débito) u 41 (Compras extratemporáneas) por simplicidad de script core.
        # Si la DGII lo pide específicamente, se duplica el flujo.
        
        env.cr.commit()
        print("\n>> BATERÍA DE SET DE PRUEBAS COMPLETADA <<")
        print("Revisar respuestas de Certia Webhooks y portal testing de la DGII.")

    except Exception as e:
        print(f"\n[X] Transacción Abortada. Error durante la generación del test set: {str(e)}")

if __name__ == "__main__":
    run_dgii_test_set(env)
