param(
    [Parameter(Mandatory = $false)]
    [string]$SubjectContains = "",

    [Parameter(Mandatory = $false)]
    [string]$StorePath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-CertificatesFromStore {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $parts = $Path -split "\\"
    if ($parts.Count -ne 2) {
        throw "StorePath invalido: $Path"
    }

    $storeLocation = [System.Security.Cryptography.X509Certificates.StoreLocation]::$($parts[0])
    $storeName = $parts[1]
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store($storeName, $storeLocation)
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
    try {
        return @($store.Certificates | Where-Object { $_.HasPrivateKey })
    }
    finally {
        $store.Close()
    }
}

$stores = if ([string]::IsNullOrWhiteSpace($StorePath)) {
    @("CurrentUser\My", "LocalMachine\My")
}
else {
    @($StorePath)
}

$all = @()
foreach ($store in $stores) {
    $items = Get-CertificatesFromStore -Path $store
    foreach ($cert in $items) {
        $all += [ordered]@{
            store = $store
            subject = $cert.Subject
            issuer = $cert.Issuer
            thumbprint = $cert.Thumbprint
            not_before = $cert.NotBefore.ToString("o")
            not_after = $cert.NotAfter.ToString("o")
        }
    }
}

if (-not [string]::IsNullOrWhiteSpace($SubjectContains)) {
    $all = @($all | Where-Object { $_.subject -like "*$SubjectContains*" })
}

[ordered]@{
    total = $all.Count
    certificates = $all
} | ConvertTo-Json -Depth 5
