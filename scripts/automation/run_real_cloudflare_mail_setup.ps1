param(
    [string]$Domain = "getupsoft.com.do",
    [string]$StartUrl = "https://dash.cloudflare.com/efce4179a7ee96c19b43c42bced58587/home/overview",
    [string]$ChromeUserDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data",
    [string]$ChromeProfileDirectory = "Default",
    [string]$MailHost = "mail.getupsoft.com.do",
    [string]$MailIPv4 = "",
    [string]$MailIPv6 = "",
    [switch]$EnableAutodiscover,
    [string]$DkimSelector = "",
    [string]$DkimValue = "",
    [string]$HubBaseUrl = "https://api.getupsoft.com.do",
    [string]$InternalSecret = ""
)

if (-not $MailIPv4) {
    throw "Debes indicar -MailIPv4 con la IP publica real del servidor Mailcow"
}

if (-not $env:CLOUDFLARE_API_TOKEN) {
    throw "Falta CLOUDFLARE_API_TOKEN en entorno"
}

$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "[1/4] Abriendo Cloudflare Dashboard con perfil Chrome real..."
& $python scripts/automation/assist_cloudflare_login.py `
    --start-url "$StartUrl" `
    --user-data-dir "$ChromeUserDataDir" `
    --profile-directory "$ChromeProfileDirectory" `
    --timeout-seconds 600
if ($LASTEXITCODE -ne 0) {
    Write-Warning "No se confirmo entrada al dashboard en tiempo esperado. Continuando con API si tienes token valido..."
}

Write-Host "[2/4] Aplicando DNS de correo en Cloudflare..."
$cmd = @(
    "scripts/automation/configure_cloudflare_mail_dns_full.py",
    "--domain", $Domain,
    "--mail-host", $MailHost,
    "--mail-ipv4", $MailIPv4,
    "--output", "docs/evidence/cloudflare_mail_dns_result.json"
)
if ($MailIPv6) { $cmd += @("--mail-ipv6", $MailIPv6) }
if ($EnableAutodiscover) { $cmd += "--enable-autodiscover" }
if ($DkimSelector -and $DkimValue) {
    $cmd += @("--dkim-selector", $DkimSelector, "--dkim-value", $DkimValue)
}
& $python @cmd
if ($LASTEXITCODE -ne 0) { throw "Fallo configurando DNS de correo" }

Write-Host "[3/4] Verificacion DNS rapida..."
nslookup -type=MX $Domain 8.8.8.8
nslookup -type=TXT $Domain 8.8.8.8
nslookup -type=TXT "_dmarc.$Domain" 8.8.8.8

Write-Host "[4/4] (Opcional) Health check del Mail Intake en EasyCounting..."
if ($InternalSecret) {
    try {
        $headers = @{ "X-Internal-Secret" = $InternalSecret }
        $resp = Invoke-RestMethod -Method Get -Uri "$HubBaseUrl/api/v1/internal/certificate-workflow/mail-intake/health" -Headers $headers
        $resp | ConvertTo-Json -Depth 5 | Set-Content "docs/evidence/mail_intake_health_after_dns.json" -Encoding UTF8
        Write-Host "Health guardado en docs/evidence/mail_intake_health_after_dns.json"
    } catch {
        Write-Warning "No se pudo consultar health interno: $($_.Exception.Message)"
    }
} else {
    Write-Host "InternalSecret no proporcionado, se omite health check interno."
}

Write-Host "Completado. Evidencia principal: docs/evidence/cloudflare_mail_dns_result.json"
