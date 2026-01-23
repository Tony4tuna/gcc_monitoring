param(
  [string]$HostName = "gcchvacr.com",
  [string]$UserName = "tony"
)

$ErrorActionPreference = "Stop"

# Project root is where this script lives
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# What to ship (add/remove if needed)
$Items = @(
  "app.py",
  "core",
  "pages",
  "ui",
  "schema",
  "data",
  "requirements.txt",
  "deploy.sh",
  "setup_server.sh"
)

# Build a clean staging folder called deployment\
$Stage = Join-Path $Root "deployment"
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path $Stage | Out-Null

foreach ($i in $Items) {
  if (Test-Path (Join-Path $Root $i)) {
    Copy-Item (Join-Path $Root $i) $Stage -Recurse -Force
  } else {
    Write-Host "WARNING: missing $i (skipping)"
  }
}

# Create tarball in project root
$TarPath = Join-Path $Root "gcc_monitoring_deploy.tar.gz"
if (Test-Path $TarPath) { Remove-Item $TarPath -Force }

# Use Windows built-in tar.exe
tar -czf $TarPath deployment

Write-Host "Uploading tarball to server..."
scp $TarPath "$UserName@$HostName`:/tmp/gcc_monitoring_deploy.tar.gz"

Write-Host "Deploying on server..."
ssh "$UserName@$HostName" "bash /home/tony/deploy_gcc_monitoring.sh"

Write-Host "`n✅ Deploy complete: https://gcchvacr.com"
