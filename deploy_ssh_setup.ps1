# SSH Key Setup & Deployment Script
# One-time setup: generates SSH key and deploys to DigitalOcean droplet
# Future deployments: use deploy_ssh_auto.ps1 (no password needed)

param(
    [switch]$SetupOnly = $false
)

$HOST = "gcchvacr.com"
$USER = "tony"
$SSH_KEY_PATH = "$env:USERPROFILE\.ssh\id_ed25519"
$APP_DIR = "/home/tony/gcc_monitoring"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SSH Key Setup & Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if SSH key exists
if (-not (Test-Path $SSH_KEY_PATH)) {
    Write-Host "📝 Step 1: Generating SSH key..." -ForegroundColor Yellow
    Write-Host "   This is a one-time setup (key will be saved securely)" -ForegroundColor Gray
    
    # Generate SSH key (no passphrase for automation)
    ssh-keygen -t ed25519 -f $SSH_KEY_PATH -N "" -C "gcc_monitoring_deploy" | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ SSH key generated at: $SSH_KEY_PATH" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Failed to generate SSH key" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ SSH key already exists at: $SSH_KEY_PATH" -ForegroundColor Green
}

# Step 2: Copy SSH key to droplet
Write-Host ""
Write-Host "🔑 Step 2: Copying SSH key to droplet..." -ForegroundColor Yellow
Write-Host "   Enter password for tony@$HOST" -ForegroundColor Gray

ssh-copy-id -i "$SSH_KEY_PATH.pub" -o StrictHostKeyChecking=no "$USER@$HOST" 2>&1 | ForEach-Object {
    if ($_ -match "added") {
        Write-Host "   ✓ SSH key added to droplet" -ForegroundColor Green
    } elseif ($_ -match "already exist") {
        Write-Host "   ✓ SSH key already on droplet" -ForegroundColor Green
    }
}

if ($SetupOnly) {
    Write-Host ""
    Write-Host "✓ SSH setup complete! You can now use:" -ForegroundColor Green
    Write-Host "   .\deploy_ssh_auto.ps1" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

# Step 3: Deploy to droplet
Write-Host ""
Write-Host "🚀 Step 3: Deploying to droplet..." -ForegroundColor Yellow

ssh -o StrictHostKeyChecking=no "$USER@$HOST" @"
    cd $APP_DIR && \
    echo '� Backing up database...' && \
    cp data/app.db data/app.db.backup_\$(date +%Y%m%d_%H%M%S) && \
    echo '   ✓ Backup created' && \
    echo '' && \
    echo '�📥 Pulling latest code from GitHub...' && \
    git pull && \
    echo '✓ Code updated' && \
    echo '' && \
    echo '🔧 Running migrations...' && \
    ./venv/bin/python utility/add_installed_location_column.py && \
    ./venv/bin/python utility/create_setpoints_table.py && \
    ./venv/bin/python utility/create_company_info_table.py && \
    echo '✓ Migrations complete' && \
    echo '' && \
    echo '🛑 Stopping old app...' && \
    pkill -u tony python ; sleep 2 && \
    echo '✓ Old app stopped' && \
    echo '' && \
    echo '▶️  Starting new app on port 8000...' && \
    nohup ./venv/bin/python app.py > app.out 2>&1 & \
    sleep 3 && \
    echo '✓ New app started' && \
    echo '' && \
    echo '🌐 App Status:' && \
    curl -s http://localhost:8000 > /dev/null && echo '✓ App responding on http://localhost:8000' || echo '⚠️  App may not be ready yet'
"@

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Deployment complete!" -ForegroundColor Green
    Write-Host "  🌐 Access: https://$HOST" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "⚠️  Deployment completed with warnings (check logs)" -ForegroundColor Yellow
    Write-Host ""
}
