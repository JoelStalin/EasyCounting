param(
    [Parameter(Mandatory = $true)]
    [string]$XmlPath,

    [Parameter(Mandatory = $true)]
    [string]$P12Path,

    [Parameter(Mandatory = $true)]
    [string]$P12Password,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = "",

    [Parameter(Mandatory = $false)]
    [string]$AppExePath = "c:\Users\yoeli\Documents\dgii_encf\tools\App Firma Digital.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $XmlPath)) {
    throw "No existe XML: $XmlPath"
}
if (-not (Test-Path -LiteralPath $P12Path)) {
    throw "No existe certificado: $P12Path"
}
if (-not (Test-Path -LiteralPath $AppExePath)) {
    throw "No existe App Firma Digital: $AppExePath"
}

try {
    Unblock-File -LiteralPath $AppExePath -ErrorAction Stop
} catch {
    # Si no aplica o ya estaba desbloqueado, continuamos.
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $dir = Split-Path -Parent $XmlPath
    $name = [System.IO.Path]::GetFileNameWithoutExtension($XmlPath)
    $OutputPath = Join-Path $dir "$name.signed.xml"
}

$asm = [Reflection.Assembly]::LoadFrom($AppExePath)
$svcType = $asm.GetType("wfFirma.Services.SignServices")
if ($null -eq $svcType) {
    throw "No se encontró wfFirma.Services.SignServices en el ejecutable."
}

$prop = $svcType.GetProperty("Current", [Reflection.BindingFlags] "Public,Static")
if ($null -eq $prop) {
    throw "No se encontró propiedad Current en SignServices."
}

$svc = $prop.GetValue($null, $null)
$doc = $svc.FirmarXml($XmlPath, $P12Path, $P12Password, $false)
$doc.Save($OutputPath)
if (-not (Test-Path -LiteralPath $OutputPath)) {
    throw "La app DGII no genero el archivo firmado: $OutputPath"
}

$result = [ordered]@{
    status = "ok"
    xml = $XmlPath
    p12 = $P12Path
    app = $AppExePath
    output = $OutputPath
}
$result | ConvertTo-Json -Depth 4
