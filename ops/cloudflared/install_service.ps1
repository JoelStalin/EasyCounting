$ErrorActionPreference = "Stop"

Write-Host "🚀 Preparando la instalacion del Tunel como Servicio de Windows (P1)..."

$serviceConfigPath = "C:\Windows\System32\config\systemprofile\.cloudflared"
if (-not (Test-Path $serviceConfigPath)) {
    New-Item -ItemType Directory -Force -Path $serviceConfigPath | Out-Null
}

$repoPath = "C:\Users\yoeli\Documents\dgii_encf"
$configFile = "$repoPath\ops\cloudflared\getupsoft.com.do.local.yml"
$credFile = "C:\Users\yoeli\.cloudflared\80297212-52f4-4f4e-b0dd-11bcd2307399.json"

Write-Host "📂 Copiando configuracion y credenciales al directorio del sistema..."
Copy-Item $configFile "$serviceConfigPath\config.yml" -Force
Copy-Item $credFile "$serviceConfigPath\" -Force

Write-Host "🛑 Deteniendo la instancia manual en background..."
Get-Process -Name cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "⚙️ Instalando el servicio persistente de Cloudflared..."
cloudflared service install

Write-Host "✅ Inicializando el servicio base..."
Start-Service cloudflared

Write-Host "=============================================="
Write-Host "🎉 TUNEL PERSISTENTE INSTALADO EXITOSAMENTE"
Write-Host "El dominio ahora esta expuesto todo el tiempo incluso si el equipo se reinicia."
Write-Host "=============================================="
Start-Sleep -Seconds 5
