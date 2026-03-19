param(
    [string]$ApiBaseUrl = "https://api.getupsoft.com.do"
)

$nodeBin = "C:\Program Files\nodejs"
$pnpmBin = Join-Path $env:APPDATA "npm"
$env:PATH = "$nodeBin;$pnpmBin;$env:PATH"
$env:VITE_API_BASE_URL = $ApiBaseUrl

Push-Location "frontend"
try {
    pnpm install
    pnpm lint
    pnpm build
}
finally {
    Pop-Location
}
