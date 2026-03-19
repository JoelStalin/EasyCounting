param(
    [string]$Distro = "Ubuntu",
    [string]$ProjectWindowsPath = "C:\Users\yoeli\Documents\dgii_encf"
)

$wslPath = $ProjectWindowsPath -replace "\\", "/"
$wslPath = "/mnt/" + $wslPath.Substring(0,1).ToLower() + $wslPath.Substring(2)

$command = @"
set -e
cd '$wslPath'
docker compose -f docker-compose.yml -f docker-compose.override.yml -f deploy/docker-compose.wsl-local.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.override.yml -f deploy/docker-compose.wsl-local.yml ps
"@

wsl.exe -d $Distro --cd $wslPath bash -lc $command
