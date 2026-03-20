# test_b2b_l10n_do.py
import sys

def execute_functional_test(env):
    try:
        # Resolver fallo de 'Validation Error: Fiscal invoices require partner fiscal type'
        partner = env['res.partner'].search([('name', '=', 'Azure Interior')], limit=1)
        if not partner:
            partner = env['res.partner'].search([('vat', '=', '101000000')], limit=1)

        print(">> Asignando fiscal_type y expense_type al Partner...")
        if hasattr(partner, 'l10n_do_expense_type'):
            partner.write({'l10n_do_expense_type': '02'}) # Gastos por trabajos
        
        # En la localizacion Getupsoft/Adhoc
        doc_type_31 = env['l10n_latam.document.type'].search([('code', '=', '31')], limit=1)
        journal = env['account.journal'].search([('type', '=', 'sale')], limit=1)
        
        print(">> Creando Factura Borrador (Draft E-CF B2B)...")
        invoice = env['account.move'].create({
            'partner_id': partner.id,
            'move_type': 'out_invoice',
            'journal_id': journal.id,
            'l10n_latam_document_type_id': doc_type_31.id if doc_type_31 else False,
            'invoice_line_ids': [(0, 0, {
                'name': 'Soporte y Consultoría DO',
                'quantity': 1,
                'price_unit': 25000.0,
            })]
        })
        
        print(f">> Confirmando Factura (Trigger Webhook hacia CERTIA)...")
        invoice.action_post()
        
        env.cr.commit()
        print(f"--> PRUEBA FUNCIONAL EXITOSA. Factura {invoice.name} (ID: {invoice.id}) en estado: {invoice.state}")

    except Exception as e:
        print(">> Error durante la prueba funcional:", str(e))

if __name__ == "__main__":
    execute_functional_test(env)
