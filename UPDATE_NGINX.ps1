# Interactive Nginx Update Script
# Opens an SSH session and guides you through Nginx updates

$HOST = "gcchvacr.com"
$USER = "tony"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Interactive Nginx Configuration Update" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will open an SSH session where you can:" -ForegroundColor Green
Write-Host "  1. Update Nginx to proxy port 8000 (instead of 8080)"
Write-Host "  2. Verify the configuration"
Write-Host "  3. Reload Nginx"
Write-Host ""
Write-Host "Commands to run (copy & paste each one):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  sudo sed -i 's/:8080/:8000/g' /etc/nginx/sites-available/default" -ForegroundColor White
Write-Host "  sudo nginx -t" -ForegroundColor White
Write-Host "  sudo systemctl reload nginx" -ForegroundColor White
Write-Host "  curl -I http://localhost" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to connect to the droplet..." -ForegroundColor Cyan
Read-Host

# Connect via SSH
ssh -o StrictHostKeyChecking=no "$USER@$HOST"

# After SSH closes, show completion message
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  ✅ Nginx update complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your app should now be live at:" -ForegroundColor Green
Write-Host "  https://gcchvacr.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "Log in with:" -ForegroundColor Green
Write-Host "  Email: admin" -ForegroundColor White
Write-Host "  Password: 1931" -ForegroundColor White
Write-Host ""
