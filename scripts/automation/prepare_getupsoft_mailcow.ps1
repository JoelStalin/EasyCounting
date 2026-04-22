param(
    [string]$SshHost = "getupsoft",
    [string]$Hostname = "mail.getupsoft.com.do",
    [string]$RemoteDir = "/opt/mailcow-dockerized",
    [string]$Timezone = "America/Santo_Domingo",
    [int]$HttpPort = 8081,
    [int]$HttpsPort = 8443,
    [string]$GitRef = "",
    [switch]$StartStack,
    [switch]$SkipDockerInstall,
    [string]$Output = "artifacts_live_dns/getupsoft_mailcow_prepare.log"
)

$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

$cmd = @(
    "scripts/automation/prepare_getupsoft_mailcow.py",
    "--ssh-host", $SshHost,
    "--hostname", $Hostname,
    "--remote-dir", $RemoteDir,
    "--timezone", $Timezone,
    "--http-port", "$HttpPort",
    "--https-port", "$HttpsPort",
    "--output", $Output
)

if ($GitRef) { $cmd += @("--git-ref", $GitRef) }
if ($StartStack) { $cmd += "--start-stack" }
if ($SkipDockerInstall) { $cmd += "--skip-docker-install" }

& $python @cmd
exit $LASTEXITCODE
