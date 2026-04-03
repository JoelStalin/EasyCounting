import xmlrpc.client

url = "http://127.0.0.1:15070"
db = "odoo15_test"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(url))
uid = common.authenticate(db, username, password, {})
if not uid:
    print("Failed to authenticate")
    exit(1)

models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(url))

print("Fetching RNC 22500706423 using onchange_partner_name logic via create")
# We test what happens if we create a partner with this VAT
partner_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{
    'name': 'Test Getupsoft RNC',
    'vat': '22500706423',
    'country_id': 62 # DO
}])

partner = models.execute_kw(db, uid, password, 'res.partner', 'read', [[partner_id]], {'fields': ['name', 'vat', 'l10n_do_dgii_tax_payer_type', 'comment']})
print("Result of create:", partner)

# clean up
models.execute_kw(db, uid, password, 'res.partner', 'unlink', [[partner_id]])
