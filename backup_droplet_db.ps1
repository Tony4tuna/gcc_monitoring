# Manual Database Backup Script
# Usage: .\backup_droplet_db.ps1
# Backs up the droplet database locally for safekeeping

param(
    [switch]$Local = $false  # If true, only backup locally; if false, backup from droplet
)

$HOST = "gcchvacr.com"
$USER = "tony"
$SSH_KEY_PATH = "$env:USERPROFILE\.ssh\id_ed25519"
$LOCAL_DB = "data/app.db"
$DROPLET_DB = "/home/tony/gcc_monitoring/data/app.db"
$BACKUP_DIR = "data/backups"

# Create backup directory if it doesn't exist
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR | Out-Null
}

$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Database Backup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($Local) {
    Write-Host "📦 Backing up local database..." -ForegroundColor Yellow
    $BACKUP_FILE = "$BACKUP_DIR/app.db.local_$TIMESTAMP"
    Copy-Item $LOCAL_DB $BACKUP_FILE
    Write-Host "✓ Backup saved: $BACKUP_FILE" -ForegroundColor Green
} else {
    Write-Host "📥 Downloading database from droplet..." -ForegroundColor Yellow
    
    # Check if SSH key exists
    if (-not (Test-Path $SSH_KEY_PATH)) {
        Write-Host "⚠️  SSH key not found. Using password auth..." -ForegroundColor Yellow
        scp -o StrictHostKeyChecking=no "$USER@$HOST`:$DROPLET_DB" "$BACKUP_DIR/app.db.droplet_$TIMESTAMP" 2>&1 | Out-Null
    } else {
        scp -i $SSH_KEY_PATH -o StrictHostKeyChecking=no "$USER@$HOST`:$DROPLET_DB" "$BACKUP_DIR/app.db.droplet_$TIMESTAMP" 2>&1 | Out-Null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Backup saved: $BACKUP_DIR/app.db.droplet_$TIMESTAMP" -ForegroundColor Green
    } else {
        Write-Host "✗ Backup failed" -ForegroundColor Red
        exit 1
    }
}

# Show all backups
Write-Host ""
Write-Host "📋 Recent backups:" -ForegroundColor Gray
Get-ChildItem $BACKUP_DIR -Filter "app.db*" -File | Sort-Object -Property LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
    $size = [math]::Round($_.Length / 1MB, 2)
    Write-Host "   $($_.Name) - $size MB - $($_.LastWriteTime)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Backup complete!" -ForegroundColor Green
Write-Host ""
