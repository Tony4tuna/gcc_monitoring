@echo off
REM Complete Deployment Finalization from Windows
REM One command to finalize everything on the droplet

setlocal enabledelayedexpansion

set HOST=gcchvacr.com
set USER=tony
set SCRIPT_PATH=/home/tony/finalize_deployment.sh

echo.
echo ================================================
echo  GCC Monitoring - Complete Deployment
echo ================================================
echo.
echo This script will:
echo  1. Initialize database schema
echo  2. Run all migrations
echo  3. Stop old app processes
echo  4. Start new app on port 8000
echo  5. Verify deployment
echo.

set /p PASSWORD="Enter your DigitalOcean password: "

if "%PASSWORD%"=="" (
    echo Error: Password required
    exit /b 1
)

echo.
echo Uploading deployment script to %HOST%...
scp -o StrictHostKeyChecking=no finalize_deployment.sh %USER%@%HOST%:%SCRIPT_PATH%

if errorlevel 1 (
    echo Error: Failed to upload script
    exit /b 1
)

echo.
echo Running deployment on droplet (this will take 30-60 seconds)...
echo.

ssh -o StrictHostKeyChecking=no %USER%@%HOST% "chmod +x %SCRIPT_PATH% && %SCRIPT_PATH%"

if errorlevel 1 (
    echo.
    echo Warning: Deployment script returned an error
    exit /b 1
)

echo.
echo ================================================
echo  ✅ App deployment complete!
echo ================================================
echo.
echo IMPORTANT: Update Nginx to proxy to port 8000
echo.
echo Run these commands on the droplet:
echo.
echo   ssh %USER%@%HOST%
echo   sudo sed -i 's/:8080/:8000/g' /etc/nginx/sites-available/default
echo   sudo nginx -t
echo   sudo systemctl reload nginx
echo.
echo Then verify:
echo   curl -I http://localhost
echo.
echo Next steps:
echo  1. Update Nginx (commands above)
echo  2. Open https://gcchvacr.com in your browser
echo  3. Log in with admin / 1931
echo  4. Navigate to Thermostat page to verify
echo.
echo If you have any issues, check the logs:
echo  - App logs: ssh %USER%@%HOST% "tail -50 ~/gcc_monitoring/app.out"
echo  - Nginx logs: ssh %USER%@%HOST% "sudo tail -50 /var/log/nginx/error.log"
echo.

pause
