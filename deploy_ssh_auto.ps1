# Fast Deployment Script (after SSH key setup)
# Usage: .\deploy_ssh_auto.ps1
# No password prompts - uses SSH key authentication

$TARGET_HOST = "gcchvacr.com"
$USER = "tony"
$SSH_KEY_PATH = "$env:USERPROFILE\.ssh\id_ed25519"
$APP_DIR = "/home/tony/gcc_monitoring"

# Check if SSH key exists
if (-not (Test-Path $SSH_KEY_PATH)) {
    Write-Host "❌ SSH key not found at: $SSH_KEY_PATH" -ForegroundColor Red
    Write-Host "   Please run: .\deploy_ssh_setup.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  GCC Monitoring - Auto Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Target: $USER@$TARGET_HOST" -ForegroundColor Gray
Write-Host "🔑 Auth:   SSH Key (no password needed)" -ForegroundColor Green
Write-Host ""

$startTime = Get-Date

# Deploy
Write-Host "🚀 Starting deployment..." -ForegroundColor Yellow
Write-Host ""

ssh -o StrictHostKeyChecking=no -i $SSH_KEY_PATH "$USER@$TARGET_HOST" @"
    set -e
    cd $APP_DIR
    
    echo '� Backing up database...'
    cp data/app.db data/app.db.backup_$(date +%Y%m%d_%H%M%S)
    echo '   ✓ Backup created'
    echo ''
    
    echo '�📥 Pulling latest code from GitHub...'
    git pull
    echo '   ✓ Code updated'
    echo ''
    
    echo '🔧 Running migrations...'
    ./venv/bin/python utility/add_installed_location_column.py > /dev/null 2>&1
    ./venv/bin/python utility/create_setpoints_table.py > /dev/null 2>&1
    ./venv/bin/python utility/create_company_info_table.py > /dev/null 2>&1
    echo '   ✓ Migrations complete'
    echo ''
    
    echo '🛑 Stopping old app processes...'
    pkill -u tony python > /dev/null 2>&1 || true
    sleep 2
    echo '   ✓ Old app stopped'
    echo ''
    
    echo '▶️  Starting new app on port 8000...'
    nohup ./venv/bin/python app.py > app.out 2>&1 &
    APP_PID=\$!
    sleep 3
    
    if ps -p \$APP_PID > /dev/null 2>&1; then
        echo "   ✓ New app started (PID: \$APP_PID)"
    else
        echo '   ⚠️  App startup check failed'
        echo '   Logs (last 20 lines):'
        tail -20 app.out
    fi
    
    echo ''
    echo '✅ Deployment complete!'
"@

$duration = ((Get-Date) - $startTime).TotalSeconds

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Deployment finished in $([math]::Round($duration, 1))s" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Access: https://$HOST" -ForegroundColor Cyan
Write-Host ""
