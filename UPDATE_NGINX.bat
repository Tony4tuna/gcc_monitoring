@echo off
REM Update Nginx to point to port 8000 (where new app runs)

set HOST=gcchvacr.com
set USER=tony

echo.
echo ================================================
echo  Nginx Configuration Update
echo ================================================
echo.
echo This will:
echo  1. Update Nginx to proxy to port 8000
echo  2. Verify Nginx configuration
echo  3. Reload Nginx
echo.

set /p PASSWORD="Enter your DigitalOcean password: "

if "%PASSWORD%"=="" (
    echo Error: Password required
    exit /b 1
)

echo.
echo Updating Nginx...
echo.

ssh -o StrictHostKeyChecking=no %USER%@%HOST% "echo %PASSWORD% | sudo -S sed -i 's/:8080/:8000/g' /etc/nginx/sites-available/default && echo %PASSWORD% | sudo -S nginx -t && echo %PASSWORD% | sudo -S systemctl reload nginx"

if errorlevel 1 (
    echo.
    echo Error: Failed to update Nginx
    exit /b 1
)

echo.
echo ================================================
echo  ✅ Nginx updated successfully!
echo ================================================
echo.
echo Verifying deployment...
ssh -o StrictHostKeyChecking=no %USER%@%HOST% "sleep 2 && curl -s -I http://localhost | head -1"

echo.
echo Your app is now live at: https://gcchvacr.com
echo.
echo Log in with:
echo   Email: admin
echo   Password: 1931
echo.

pause
