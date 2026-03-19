param(
    [string]$Browser = "chrome",
    [int]$SlowMoMs = 900,
    [int]$KeepOpenMs = 2000,
    [string]$AdminBaseUrl = "",
    [string]$ClientBaseUrl = "",
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
if ($ApiBaseUrl) {
    $env:API_BASE_URL = $ApiBaseUrl
}

.\.venv\Scripts\python -m pytest e2e `
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
