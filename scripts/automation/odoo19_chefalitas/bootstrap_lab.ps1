param(
    [string]$ComposeFile = "labs/odoo19_chefalitas/docker-compose.yml",
    [string]$Database = "chefalitas19lab"
)

$root = Resolve-Path "."
$composePath = Join-Path $root $ComposeFile

if (-not (Test-Path $composePath)) {
    throw "No se encontro el compose del laboratorio: $composePath"
}

docker compose -f $composePath up -d --build db
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo iniciar la base del laboratorio Odoo"
}

docker compose -f $composePath run --rm odoo odoo `
    -c /etc/odoo/odoo.conf `
    -d $Database `
    -i base,account,l10n_do,l10n_latam_invoice_document,getupsoft_l10n_do_accounting,getupsoft_l10n_do_accounting_report `
    --without-demo=True `
    --stop-after-init
if ($LASTEXITCODE -ne 0) {
    throw "Fallo la inicializacion del laboratorio Odoo 19"
}

docker compose -f $composePath up -d odoo
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo levantar Odoo 19"
}

Get-Content -Raw "scripts/automation/odoo19_chefalitas/provision_lab_odoo.py" | docker compose -f $composePath exec -T odoo odoo shell `
    -c /etc/odoo/odoo.conf `
    -d $Database
if ($LASTEXITCODE -ne 0) {
    throw "Fallo la provision del laboratorio Odoo 19"
}
