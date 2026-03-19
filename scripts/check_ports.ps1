# Windows port check and firewall rules for DGII
$Ports = @(80, 443)

Write-Host "Checking ports:" ($Ports -join ", ")
foreach ($p in $Ports) {
  $inUse = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
  if ($inUse) {
    Write-Host "Port $p in use"
  } else {
    Write-Host "Port $p free"
  }
}

# Uncomment to open firewall ports
# New-NetFirewallRule -DisplayName "DGII HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
# New-NetFirewallRule -DisplayName "DGII HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
