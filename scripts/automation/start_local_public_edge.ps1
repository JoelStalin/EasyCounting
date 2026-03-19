param(
    [int]$CorporatePort = 18085,
    [int]$AdminPort = 18081,
    [int]$ClientPort = 18082,
    [int]$SellerPort = 18084,
    [int]$ApexPort = 18083,
    [int]$ApiPort = 28080,
    [string]$ApiBaseUrl = "",
    [string]$CorporatePublicBaseUrl = "https://www.getupsoft.com.do",
    [string]$AdminPublicBaseUrl = "https://admin.getupsoft.com.do",
    [string]$ClientPublicBaseUrl = "https://cliente.getupsoft.com.do",
    [string]$SellerPublicBaseUrl = "https://socios.getupsoft.com.do",
    [string]$ApexRedirectTarget = "https://www.getupsoft.com.do",
    [switch]$StartDocker
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
$corporateDist = Join-Path $root "frontend\apps\corporate-portal\dist"
$adminDist = Join-Path $root "frontend\apps\admin-portal\dist"
$clientDist = Join-Path $root "frontend\apps\client-portal\dist"
$sellerDist = Join-Path $root "frontend\apps\seller-portal\dist"
$serverScript = Join-Path $root "scripts\automation\serve_spa.py"

if ([string]::IsNullOrWhiteSpace($ApiBaseUrl)) {
    $ApiBaseUrl = "http://127.0.0.1:$ApiPort"
}

if ($StartDocker) {
    docker compose -f docker-compose.yml -f deploy/docker-compose.wsl-local.yml up -d --build
}

if (-not $python) {
    throw "No se encontro Python del entorno virtual en .venv ni .venv312"
}
if (-not (Test-Path $corporateDist)) {
    throw "No existe dist de corporate-portal en $corporateDist"
}
if (-not (Test-Path $adminDist)) {
    throw "No existe dist de admin-portal en $adminDist"
}
if (-not (Test-Path $clientDist)) {
    throw "No existe dist de client-portal en $clientDist"
}
if (-not (Test-Path $sellerDist)) {
    throw "No existe dist de seller-portal en $sellerDist"
}

Start-Process -FilePath $python -ArgumentList @(
    $serverScript,
    "--dir", $corporateDist,
    "--port", "$CorporatePort"
) -WindowStyle Minimized
Start-Process -FilePath $python -ArgumentList @(
    $serverScript,
    "--dir", $adminDist,
    "--port", "$AdminPort",
    "--runtime-api-base-url", $AdminPublicBaseUrl,
    "--proxy-api-base-url", "http://127.0.0.1:$ApiPort"
) -WindowStyle Minimized
Start-Process -FilePath $python -ArgumentList @(
    $serverScript,
    "--dir", $clientDist,
    "--port", "$ClientPort",
    "--runtime-api-base-url", $ClientPublicBaseUrl,
    "--proxy-api-base-url", "http://127.0.0.1:$ApiPort"
) -WindowStyle Minimized
Start-Process -FilePath $python -ArgumentList @(
    $serverScript,
    "--dir", $sellerDist,
    "--port", "$SellerPort",
    "--runtime-api-base-url", $SellerPublicBaseUrl,
    "--proxy-api-base-url", "http://127.0.0.1:$ApiPort"
) -WindowStyle Minimized
Start-Process -FilePath $python -ArgumentList @($serverScript, "--port", "$ApexPort", "--redirect-target", $ApexRedirectTarget) -WindowStyle Minimized

Write-Output "Corporate site: http://127.0.0.1:$CorporatePort"
Write-Output "Admin portal:  http://127.0.0.1:$AdminPort"
Write-Output "Client portal: http://127.0.0.1:$ClientPort"
Write-Output "Seller portal: http://127.0.0.1:$SellerPort"
Write-Output "Apex redirect: http://127.0.0.1:$ApexPort"
Write-Output "API proxy:     http://127.0.0.1:$ApiPort"
Write-Output ""
Write-Output "Siguiente paso recomendado:"
Write-Output "cloudflared tunnel --config ops/cloudflared/getupsoft.com.do.example.yml run"
