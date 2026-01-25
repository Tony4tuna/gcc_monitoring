# GCC Monitoring System - Automatic Setup Script
# Run this script as Administrator to automatically set up the application

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "❌ This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "🚀 GCC Monitoring System - Automatic Installation" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python Installation
Write-Host "📦 Step 1: Checking Python installation..." -ForegroundColor Green
$pythonCheck = python --version 2>&1

if ($pythonCheck -like "*Python 3*") {
    Write-Host "✅ Python found: $pythonCheck" -ForegroundColor Green
} else {
    Write-Host "❌ Python 3.12 not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.12 from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Read-Host "Press Enter after installing Python"
    exit
}

Write-Host ""

# Step 2: Create Virtual Environment
Write-Host "🔧 Step 2: Creating virtual environment..." -ForegroundColor Green

if (Test-Path "venv") {
    Write-Host "   Virtual environment already exists, skipping..." -ForegroundColor Yellow
} else {
    Write-Host "   Creating new virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

Write-Host ""

# Step 3: Activate Virtual Environment
Write-Host "📦 Step 3: Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"
Write-Host "✅ Virtual environment activated" -ForegroundColor Green

Write-Host ""

# Step 4: Install Dependencies
Write-Host "📥 Step 4: Installing dependencies..." -ForegroundColor Green
Write-Host "   (This may take 2-3 minutes...)" -ForegroundColor Cyan

pip install --upgrade pip -q
pip install nicegui passlib -q

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies!" -ForegroundColor Red
    Write-Host "Try running manually: pip install nicegui passlib" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host ""

# Step 5: Verify Installation
Write-Host "🔍 Step 5: Verifying installation..." -ForegroundColor Green

$niceguiCheck = pip show nicegui 2>&1
$passlibCheck = pip show passlib 2>&1

if ($niceguiCheck -and $passlibCheck) {
    Write-Host "✅ All dependencies verified" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: Some dependencies may not be installed correctly" -ForegroundColor Yellow
}

Write-Host ""

# Step 6: Start Application
Write-Host "🎯 Step 6: Starting application..." -ForegroundColor Green
Write-Host ""
Write-Host "═════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
Write-Host "═════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Application starting on: http://localhost:8080" -ForegroundColor Yellow
Write-Host "🔐 Default Login:" -ForegroundColor Yellow
Write-Host "   Email: admin" -ForegroundColor White
Write-Host "   Password: 1931" -ForegroundColor White
Write-Host ""
Write-Host "To stop the app, press Ctrl + C" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting application..." -ForegroundColor Cyan
Write-Host ""

# Start the app
python app.py
