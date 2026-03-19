param(
    [ValidateSet("api", "admin", "client")]
    [string]$Target = "api"
)

$serviceUrl = switch ($Target) {
    "api" { "http://127.0.0.1:28080" }
    "admin" { "http://127.0.0.1:18081" }
    "client" { "http://127.0.0.1:18082" }
}

$cloudflared = if (Get-Command cloudflared.exe -ErrorAction SilentlyContinue) {
    (Get-Command cloudflared.exe).Source
} elseif (Test-Path "C:\Program Files (x86)\cloudflared\cloudflared.exe") {
    "C:\Program Files (x86)\cloudflared\cloudflared.exe"
} else {
    "C:\Program Files\cloudflared\cloudflared.exe"
}

& $cloudflared tunnel --url $serviceUrl
