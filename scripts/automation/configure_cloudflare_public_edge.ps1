param(
    [string]$ApiToken = $env:CLOUDFLARE_API_TOKEN,
    [string]$Domain = "getupsoft.com.do",
    [string]$AccountId = "",
    [string]$TunnelName = "getupsoft-local",
    [string]$ApiHostname = "",
    [string]$AdminHostname = "",
    [string]$ClientHostname = "",
    [string]$ApiOrigin = "http://127.0.0.1:28080",
    [string]$AdminOrigin = "http://127.0.0.1:28080",
    [string]$ClientOrigin = "http://127.0.0.1:28080",
    [string]$ApexOrigin = "http://127.0.0.1:28080",
    [string]$ApexRedirectTarget = "",
    [switch]$CreateZoneIfMissing,
    [switch]$InstallTunnelService
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $ApiHostname) {
    $ApiHostname = "api.$Domain"
}
if (-not $AdminHostname) {
    $AdminHostname = "admin.$Domain"
}
if (-not $ClientHostname) {
    $ClientHostname = "cliente.$Domain"
}
if (-not $ApexRedirectTarget) {
    $ApexRedirectTarget = "https://$AdminHostname"
}

function Invoke-CloudflareApi {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("GET", "POST", "PUT", "PATCH", "DELETE")]
        [string]$Method,
        [Parameter(Mandatory = $true)][string]$Path,
        [object]$Body = $null,
        [switch]$AllowNotFound
    )

    if (-not $ApiToken) {
        throw "Falta CLOUDFLARE_API_TOKEN. Exportalo o pasalo por -ApiToken."
    }

    $uri = "https://api.cloudflare.com/client/v4$Path"
    $headers = @{
        Authorization = "Bearer $ApiToken"
    }
    $invokeParams = @{
        Method      = $Method
        Uri         = $uri
        Headers     = $headers
        ContentType = "application/json"
    }
    if ($null -ne $Body) {
        $invokeParams.Body = ($Body | ConvertTo-Json -Depth 20 -Compress)
    }

    try {
        $response = Invoke-RestMethod @invokeParams
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($AllowNotFound -and $statusCode -eq 404) {
            return $null
        }
        $details = ""
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            if ($stream) {
                $reader = New-Object System.IO.StreamReader($stream)
                $details = $reader.ReadToEnd()
                $reader.Dispose()
            }
        }
        catch {
        }
        throw "Cloudflare API $Method $Path fallo con status $statusCode. $details"
    }

    if ($null -eq $response) {
        throw "Cloudflare API $Method $Path devolvio una respuesta vacia."
    }
    if ($response.PSObject.Properties.Name -contains "success" -and -not $response.success) {
        $errors = @()
        if ($response.errors) {
            $errors = $response.errors | ForEach-Object { $_.message }
        }
        throw "Cloudflare API $Method $Path devolvio success=false. $($errors -join '; ')"
    }

    return $response
}

function Ensure-Zone {
    $encodedName = [uri]::EscapeDataString($Domain)
    $zones = Invoke-CloudflareApi -Method GET -Path "/zones?name=$encodedName"
    $zone = $zones.result | Where-Object { $_.name -eq $Domain } | Select-Object -First 1

    if (-not $zone) {
        if (-not $CreateZoneIfMissing) {
            throw "La zona $Domain no existe en Cloudflare. Reejecuta con -CreateZoneIfMissing y -AccountId, o crea la zona manualmente."
        }
        if (-not $AccountId) {
            throw "Para crear la zona falta -AccountId."
        }

        $created = Invoke-CloudflareApi -Method POST -Path "/zones" -Body @{
            account = @{ id = $AccountId }
            name    = $Domain
            type    = "full"
        }
        $zone = $created.result
        Write-Host "Zona creada: $($zone.name) ($($zone.id))"
    }

    if (-not $AccountId) {
        $AccountId = [string]$zone.account.id
    }

    if ($zone.status -ne "active") {
        $nameServers = @($zone.name_servers) -join ", "
        throw "La zona $Domain existe pero no esta activa (status=$($zone.status)). Cambia los nameservers en el registrador a: $nameServers"
    }

    return $zone
}

function Ensure-Tunnel {
    param(
        [Parameter(Mandatory = $true)][string]$CfAccountId
    )

    $tunnels = Invoke-CloudflareApi -Method GET -Path "/accounts/$CfAccountId/cfd_tunnel?is_deleted=false"
    $tunnel = $tunnels.result | Where-Object { $_.name -eq $TunnelName } | Select-Object -First 1

    if (-not $tunnel) {
        $created = Invoke-CloudflareApi -Method POST -Path "/accounts/$CfAccountId/cfd_tunnel" -Body @{
            name       = $TunnelName
            config_src = "cloudflare"
        }
        $tunnel = $created.result
        Write-Host "Tunnel creado: $TunnelName ($($tunnel.id))"
    }
    else {
        Write-Host "Tunnel existente reutilizado: $TunnelName ($($tunnel.id))"
    }

    return $tunnel
}

function Set-TunnelIngress {
    param(
        [Parameter(Mandatory = $true)][string]$CfAccountId,
        [Parameter(Mandatory = $true)][string]$TunnelId
    )

    $payload = @{
        config = @{
            ingress = @(
                @{
                    hostname      = $Domain
                    service       = $ApexOrigin
                    originRequest = @{}
                },
                @{
                    hostname      = $ApiHostname
                    service       = $ApiOrigin
                    originRequest = @{}
                },
                @{
                    hostname      = $AdminHostname
                    service       = $AdminOrigin
                    originRequest = @{}
                },
                @{
                    hostname      = $ClientHostname
                    service       = $ClientOrigin
                    originRequest = @{}
                },
                @{
                    service = "http_status:404"
                }
            )
        }
    }

    Invoke-CloudflareApi -Method PUT -Path "/accounts/$CfAccountId/cfd_tunnel/$TunnelId/configurations" -Body $payload | Out-Null
    Write-Host "Ingress remoto actualizado para tunnel $TunnelId"
}

function Ensure-CnameRecord {
    param(
        [Parameter(Mandatory = $true)][string]$ZoneId,
        [Parameter(Mandatory = $true)][string]$Hostname,
        [Parameter(Mandatory = $true)][string]$Target
    )

    $encodedName = [uri]::EscapeDataString($Hostname)
    $records = Invoke-CloudflareApi -Method GET -Path "/zones/$ZoneId/dns_records?type=CNAME&name=$encodedName"
    $existing = $records.result | Where-Object { $_.name -eq $Hostname } | Select-Object -First 1
    $body = @{
        type    = "CNAME"
        proxied = $true
        name    = $Hostname
        content = $Target
    }

    if ($existing) {
        if ($existing.content -eq $Target -and $existing.proxied) {
            Write-Host "DNS OK: $Hostname -> $Target"
            return $existing
        }
        $updated = Invoke-CloudflareApi -Method PUT -Path "/zones/$ZoneId/dns_records/$($existing.id)" -Body $body
        Write-Host "DNS actualizado: $Hostname -> $Target"
        return $updated.result
    }

    $created = Invoke-CloudflareApi -Method POST -Path "/zones/$ZoneId/dns_records" -Body $body
    Write-Host "DNS creado: $Hostname -> $Target"
    return $created.result
}

function Ensure-ApexRedirectRule {
    param(
        [Parameter(Mandatory = $true)][string]$ZoneId
    )

    $ruleRef = "redirect_apex_to_admin"
    $rule = @{
        ref                = $ruleRef
        description        = "Redirect apex traffic to admin portal"
        expression         = "http.host eq `"$Domain`""
        action             = "redirect"
        enabled            = $true
        action_parameters  = @{
            from_value = @{
                target_url = @{
                    expression = "concat(`"$ApexRedirectTarget`", http.request.uri.path)"
                }
                status_code           = 301
                preserve_query_string = $true
            }
        }
    }

    $entrypoint = Invoke-CloudflareApi -Method GET -Path "/zones/$ZoneId/rulesets/phases/http_request_dynamic_redirect/entrypoint" -AllowNotFound

    if (-not $entrypoint) {
        Invoke-CloudflareApi -Method POST -Path "/zones/$ZoneId/rulesets" -Body @{
            name  = "Redirect rules ruleset"
            kind  = "zone"
            phase = "http_request_dynamic_redirect"
            rules = @($rule)
        } | Out-Null
        Write-Host "Ruleset de redirect creado para apex -> admin"
        return
    }

    $existingRules = @($entrypoint.result.rules | Where-Object { $_.ref -ne $ruleRef })
    $updatedRules = @($existingRules + $rule)

    Invoke-CloudflareApi -Method PUT -Path "/zones/$ZoneId/rulesets/$($entrypoint.result.id)" -Body @{
        name  = $entrypoint.result.name
        kind  = $entrypoint.result.kind
        phase = $entrypoint.result.phase
        rules = $updatedRules
    } | Out-Null
    Write-Host "Ruleset de redirect actualizado para apex -> admin"
}

function Get-TunnelToken {
    param(
        [Parameter(Mandatory = $true)][string]$CfAccountId,
        [Parameter(Mandatory = $true)][string]$TunnelId
    )

    $response = Invoke-CloudflareApi -Method GET -Path "/accounts/$CfAccountId/cfd_tunnel/$TunnelId/token"
    if ($response.result -is [string]) {
        return [string]$response.result
    }
    if ($response.result.token) {
        return [string]$response.result.token
    }
    throw "No fue posible extraer el token del tunnel $TunnelId."
}

function Install-CloudflaredTunnelService {
    param(
        [Parameter(Mandatory = $true)][string]$TunnelToken
    )

    $cloudflaredCmd = Get-Command cloudflared.exe -ErrorAction SilentlyContinue
    if (-not $cloudflaredCmd) {
        $cloudflaredCmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    }
    if (-not $cloudflaredCmd) {
        $candidatePaths = @(
            "C:\Program Files (x86)\cloudflared\cloudflared.exe",
            "C:\Program Files\cloudflared\cloudflared.exe"
        )
        foreach ($candidate in $candidatePaths) {
            if (Test-Path $candidate) {
                $cloudflaredCmd = @{ Source = $candidate }
                break
            }
        }
    }
    if (-not $cloudflaredCmd) {
        throw "cloudflared no esta instalado o no esta en PATH."
    }

    & $cloudflaredCmd.Source service install $TunnelToken
    Write-Host "Servicio cloudflared instalado/actualizado"
}

$zone = Ensure-Zone
$cfAccountId = if ($AccountId) { $AccountId } else { [string]$zone.account.id }
$tunnel = Ensure-Tunnel -CfAccountId $cfAccountId

Set-TunnelIngress -CfAccountId $cfAccountId -TunnelId $tunnel.id

$tunnelDnsTarget = "$($tunnel.id).cfargotunnel.com"
Ensure-CnameRecord -ZoneId $zone.id -Hostname $Domain -Target $tunnelDnsTarget | Out-Null
Ensure-CnameRecord -ZoneId $zone.id -Hostname $ApiHostname -Target $tunnelDnsTarget | Out-Null
Ensure-CnameRecord -ZoneId $zone.id -Hostname $AdminHostname -Target $tunnelDnsTarget | Out-Null
Ensure-CnameRecord -ZoneId $zone.id -Hostname $ClientHostname -Target $tunnelDnsTarget | Out-Null
Ensure-ApexRedirectRule -ZoneId $zone.id

$tunnelToken = Get-TunnelToken -CfAccountId $cfAccountId -TunnelId $tunnel.id
if ($InstallTunnelService) {
    Install-CloudflaredTunnelService -TunnelToken $tunnelToken
}

[pscustomobject]@{
    domain               = $Domain
    zone_id              = $zone.id
    account_id           = $cfAccountId
    zone_status          = $zone.status
    tunnel_id            = $tunnel.id
    tunnel_name          = $tunnel.name
    tunnel_status        = $tunnel.status
    api_hostname         = $ApiHostname
    admin_hostname       = $AdminHostname
    client_hostname      = $ClientHostname
    apex_redirect_target = $ApexRedirectTarget
    nameservers          = @($zone.name_servers)
    service_installable  = [bool]$tunnelToken
} | Format-List
