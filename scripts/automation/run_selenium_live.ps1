param(
    [string]$Browser = "chrome",
    [int]$SlowMoMs = 900,
    [int]$KeepOpenMs = 2000,
    [string]$AdminBaseUrl = "",
    [string]$ClientBaseUrl = "",
    [string]$SellerBaseUrl = "",
    [string]$CorporateBaseUrl = "",
    [string]$ApiBaseUrl = ""
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$artifactDir = Join-Path "e2e\artifacts" "live_$timestamp"
$reportPath = Join-Path $artifactDir "report.html"

New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

$env:HEADLESS = "0"
$env:BROWSER = $Browser
$env:SLOW_MO_MS = "$SlowMoMs"
$env:KEEP_OPEN_MS = "$KeepOpenMs"
$env:ARTIFACTS_DIR = (Resolve-Path $artifactDir).Path
if ($AdminBaseUrl) {
    $env:ADMIN_BASE_URL = $AdminBaseUrl
}
if ($ClientBaseUrl) {
    $env:CLIENT_BASE_URL = $ClientBaseUrl
}
if ($SellerBaseUrl) {
    $env:SELLER_BASE_URL = $SellerBaseUrl
}
if ($CorporateBaseUrl) {
    $env:CORPORATE_BASE_URL = $CorporateBaseUrl
}
if ($ApiBaseUrl) {
    $env:API_BASE_URL = $ApiBaseUrl
}

$pythonCandidates = @(
    ".\.venv\Scripts\python.exe",
    ".\.venv312\Scripts\python.exe"
)
$python = $pythonCandidates |
    Where-Object {
        if (-not (Test-Path $_)) { return $false }
        $venvRoot = Split-Path (Split-Path $_ -Parent) -Parent
        return Test-Path (Join-Path $venvRoot "pyvenv.cfg")
    } |
    Select-Object -First 1
if (-not $python) {
    throw "No se encontro Python del entorno virtual en .venv ni .venv312"
}

& $python -m pytest e2e `
  --html="$reportPath" `
  --self-contained-html

$exitCode = $LASTEXITCODE

if (Test-Path $reportPath) {
    Start-Process $reportPath
}
if (Test-Path $artifactDir) {
    Start-Process $artifactDir
}

exit $exitCode
