param(
  [string]$HostName = "gcchvacr.com",
  [string]$UserName = "tony",
  [string]$Password = "Fortuna2017"
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
  "utility",
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
scp $TarPath "$UserName@$HostName`:/home/$UserName/gcc_monitoring_deploy.tar.gz"

Write-Host "Deploying on server..."
# Use LF line endings for the remote script
$remoteScript = "set -e`n" +
"UPLOAD=/home/`$USER/gcc_monitoring_deploy.tar.gz`n" +
"WORK=/home/`$USER/gcc_deploy_work`n" +
"DEST=/home/`$USER/gcc_monitoring`n" +
"`n" +
"rm -rf `"`$WORK`"`n" +
"mkdir -p `"`$WORK`"`n" +
"tar -xzf `"`$UPLOAD`" -C `"`$WORK`"`n" +
"mkdir -p `"`$DEST`"`n" +
"rsync -a `"`$WORK/deployment/`" `"`$DEST/`"`n" +
"cd `"`$DEST`"`n" +
"`n" +
"python3 -m venv venv`n" +
"source venv/bin/activate`n" +
"pip install --upgrade pip -q`n" +
"pip install -r requirements.txt -q`n" +
"`n" +
"venv/bin/python utility/add_installed_location_column.py`n" +
"venv/bin/python utility/create_setpoints_table.py`n" +
"`n" +
"pkill -f `"python.*app.py`" || true`n" +
"sleep 2`n" +
"`n" +
"printf `"ADMIN_EMAIL=admin\nADMIN_PASSWORD=1931\nHOST=0.0.0.0\nPORT=8000\nSTORAGE_SECRET=devsecret\n`" > .env`n" +
"`n" +
"nohup venv/bin/python app.py > `"`$DEST/app.out`" 2>&1 &`n" +
"sleep 3`n" +
"`n" +
"echo `"App restarted on port 8000`"`n" +
"pgrep -f `"python.*app.py`" && echo `"Process running`" || echo `"No process found`"`n" +
"tail -30 `"`$DEST/app.out`"`n"

$remoteScript | ssh "$UserName@$HostName" "bash -s"

Write-Host "`n✅ Deploy attempted: https://$HostName"
