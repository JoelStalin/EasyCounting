param(
  [string]$BaseUrl = "http://localhost:8080",
  [string]$AdminEmail = "ceo",
  [string]$AdminPassword = "CHANGE_ME"
)

$ErrorActionPreference = "Stop"

Write-Host "BaseUrl: $BaseUrl"

# 1) Login
$loginBody = @{ email = $AdminEmail; password = $AdminPassword } | ConvertTo-Json
$loginResp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/auth/login" -ContentType "application/json" -Body $loginBody

if (-not $loginResp.access_token) {
  throw "No access_token in login response. If MFA is enabled you must verify MFA first."
}

$token = $loginResp.access_token
Write-Host "Got access token." 

# 2) Me
$meResp = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/me" -Headers @{ Authorization = "Bearer $token" }
Write-Host "Me OK: $($meResp.user.email)"

# 3) Admin tenants
$tenants = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/admin/tenants" -Headers @{ Authorization = "Bearer $token" }
Write-Host "Tenants: $($tenants.Count)"

# 4) Metrics
try {
  $metrics = Invoke-WebRequest -Method Get -Uri "$BaseUrl/metrics"
  Write-Host "Metrics OK: $($metrics.StatusCode)"
} catch {
  Write-Host "Metrics not available: $($_.Exception.Message)"
}

Write-Host "Done."
