param(
    [Parameter(Mandatory = $true)]
    [string]$XmlPath,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = "",

    [Parameter(Mandatory = $false)]
    [string]$StorePath = "CurrentUser\My",

    [Parameter(Mandatory = $false)]
    [string]$Thumbprint = "",

    [Parameter(Mandatory = $false)]
    [string]$SubjectContains = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$securityXmlLoaded = $false
$assemblyCandidates = @(
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Security.dll",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\System.Security.dll"
)
foreach ($candidate in $assemblyCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        [void][Reflection.Assembly]::LoadFile($candidate)
        $securityXmlLoaded = $true
        break
    }
}
if (-not $securityXmlLoaded) {
    throw "No se pudo cargar System.Security.dll para usar SignedXml."
}

if (-not (Test-Path -LiteralPath $XmlPath)) {
    throw "No existe XML: $XmlPath"
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $dir = Split-Path -Parent $XmlPath
    $name = [System.IO.Path]::GetFileNameWithoutExtension($XmlPath)
    $OutputPath = Join-Path $dir "$name.signed.xml"
}

$storePathParts = $StorePath -split "\\"
if ($storePathParts.Count -ne 2) {
    throw "StorePath invalido. Formato esperado: CurrentUser\\My o LocalMachine\\My"
}

$storeLocationName = $storePathParts[0]
$storeName = $storePathParts[1]
$storeLocation = [System.Security.Cryptography.X509Certificates.StoreLocation]::$storeLocationName
$store = New-Object System.Security.Cryptography.X509Certificates.X509Store($storeName, $storeLocation)
$store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)

try {
    $normalizedThumbprint = ($Thumbprint -replace "\s", "").ToUpperInvariant()
    $matches = @($store.Certificates | Where-Object { $_.HasPrivateKey })

    if (-not [string]::IsNullOrWhiteSpace($normalizedThumbprint)) {
        $matches = @($matches | Where-Object { $_.Thumbprint.ToUpperInvariant() -eq $normalizedThumbprint })
    }

    if (-not [string]::IsNullOrWhiteSpace($SubjectContains)) {
        $matches = @($matches | Where-Object { $_.Subject -like "*$SubjectContains*" })
    }

    if ($matches.Count -eq 0) {
        throw "No se encontro certificado con llave privada que cumpla los filtros en $StorePath"
    }

    $cert = $matches | Sort-Object NotAfter -Descending | Select-Object -First 1
    $privateKey = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
    if ($null -eq $privateKey) {
        $privateKey = $cert.PrivateKey
    }
    if ($null -eq $privateKey) {
        throw "El certificado seleccionado no expone llave privada RSA para firmado"
    }

    $xmlDoc = New-Object System.Xml.XmlDocument
    $xmlDoc.PreserveWhitespace = $true
    $xmlDoc.Load($XmlPath)

    $signedXml = New-Object System.Security.Cryptography.Xml.SignedXml($xmlDoc)
    $signedXml.SigningKey = $privateKey
    $signedXml.SignedInfo.CanonicalizationMethod = [System.Security.Cryptography.Xml.SignedXml]::XmlDsigCanonicalizationUrl
    $signedXml.SignedInfo.SignatureMethod = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"

    $reference = New-Object System.Security.Cryptography.Xml.Reference
    $reference.Uri = ""
    $reference.AddTransform((New-Object System.Security.Cryptography.Xml.XmlDsigEnvelopedSignatureTransform))
    $reference.DigestMethod = "http://www.w3.org/2001/04/xmlenc#sha256"
    $signedXml.AddReference($reference)

    $keyInfo = New-Object System.Security.Cryptography.Xml.KeyInfo
    $keyInfo.AddClause((New-Object System.Security.Cryptography.Xml.KeyInfoX509Data($cert)))
    $signedXml.KeyInfo = $keyInfo
    $signedXml.ComputeSignature()

    $xmlSignature = $signedXml.GetXml()
    [void]$xmlDoc.DocumentElement.AppendChild($xmlDoc.ImportNode($xmlSignature, $true))
    $xmlDoc.Save($OutputPath)

    $result = [ordered]@{
        status = "ok"
        xml = $XmlPath
        output = $OutputPath
        store = $StorePath
        thumbprint = $cert.Thumbprint
        subject = $cert.Subject
        issuer = $cert.Issuer
        not_before = $cert.NotBefore.ToString("o")
        not_after = $cert.NotAfter.ToString("o")
    }
    $result | ConvertTo-Json -Depth 4
}
finally {
    $store.Close()
}
