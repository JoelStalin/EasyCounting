param(
    [string]$DemoDatabaseName = "dgii_demo_lab",
    [int]$DemoApiPort = 28180,
    [int]$DemoAdminPort = 18181,
    [int]$DemoClientPort = 18182,
    [int]$DemoSellerPort = 18184,
    [int]$DemoApexPort = 18183
)

$root = Resolve-Path "."
$pythonCandidates = @(
    (Join-Path $root ".venv\Scripts\python.exe"),
    (Join-Path $root ".venv312\Scripts\python.exe")
)
$python = $pythonCandidates |
    Where-Object {
        if (-not (Test-Path $_)) { return $false }
        $venvRoot = Split-Path (Split-Path $_ -Parent) -Parent
        return Test-Path (Join-Path $venvRoot "pyvenv.cfg")
    } |
    Select-Object -First 1
$setupScript = Join-Path $root "scripts\automation\setup_demo_environment.py"
$publicEdgeScript = Join-Path $root "scripts\automation\start_local_public_edge.ps1"

if (-not $python) {
    throw "No se encontro Python del entorno virtual en .venv ni .venv312"
}

& $python $setupScript --database-name $DemoDatabaseName
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo preparar la base demo $DemoDatabaseName"
}

$env:DEMO_DATABASE_NAME = $DemoDatabaseName
$env:DEMO_API_PORT = "$DemoApiPort"
docker compose -f docker-compose.yml -f deploy/docker-compose.demo.yml up -d --build web_demo
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo levantar web_demo"
}

powershell -ExecutionPolicy Bypass -File $publicEdgeScript `
    -AdminPort $DemoAdminPort `
    -ClientPort $DemoClientPort `
    -SellerPort $DemoSellerPort `
    -ApexPort $DemoApexPort `
    -ApiPort $DemoApiPort `
    -AdminPublicBaseUrl "http://127.0.0.1:$DemoAdminPort" `
    -ClientPublicBaseUrl "http://127.0.0.1:$DemoClientPort" `
    -SellerPublicBaseUrl "http://127.0.0.1:$DemoSellerPort" `
    -ApexRedirectTarget "http://127.0.0.1:$DemoAdminPort"

Write-Output ""
Write-Output "Demo API:     http://127.0.0.1:$DemoApiPort"
Write-Output "Demo admin:   http://127.0.0.1:$DemoAdminPort"
Write-Output "Demo client:  http://127.0.0.1:$DemoClientPort"
Write-Output "Demo seller:  http://127.0.0.1:$DemoSellerPort"
Write-Output "Demo apex:    http://127.0.0.1:$DemoApexPort"
Write-Output ""
Write-Output "Credenciales demo:"
Write-Output "  admin@getupsoft.com.do / ChangeMe123!"
Write-Output "  cliente@getupsoft.com.do / Tenant123!"
Write-Output "  seller@getupsoft.com.do / Seller123!"
Write-Output "  seller.auditor@getupsoft.com.do / SellerAudit123!"
