@echo off
REM Simple deployment package creator for DigitalOcean
REM Creates a clean package ready to upload

echo ========================================
echo GCC Monitoring - Deployment Package
echo ========================================
echo.

REM Clean up old deployment
if exist gcc_monitoring_deploy.tar.gz del /f gcc_monitoring_deploy.tar.gz
if exist deployment rmdir /s /q deployment

REM Create deployment directory
mkdir deployment
echo [1/3] Creating deployment folder...

REM Copy only production files
echo [2/3] Copying files...
xcopy /E /I /Y /Q core deployment\core
xcopy /E /I /Y /Q pages deployment\pages
xcopy /E /I /Y /Q ui deployment\ui
xcopy /E /I /Y /Q schema deployment\schema

REM Copy essential root files only
copy /Y app.py deployment\ >nul
copy /Y requirements.txt deployment\ >nul
copy /Y .env.example deployment\ >nul
copy /Y deploy.sh deployment\ >nul
copy /Y setup_server.sh deployment\ >nul
copy /Y .gitignore deployment\ >nul

REM Copy database if exists
if exist data\app.db (
    mkdir deployment\data
    copy /Y data\app.db deployment\data\ >nul
    echo     - Database included
) else (
    echo     - No database found (will initialize on server)
)

REM Create archive
echo [3/3] Creating archive...
tar -czf gcc_monitoring_deploy.tar.gz deployment >nul 2>&1

REM Cleanup
rmdir /s /q deployment

echo.
echo ========================================
echo SUCCESS! Package created
echo ========================================
echo.
echo File: gcc_monitoring_deploy.tar.gz
echo Size: 
dir gcc_monitoring_deploy.tar.gz | findstr "gcc_monitoring"
echo.
echo ========================================
echo UPLOAD TO YOUR DROPLET:
echo ========================================
echo.
echo scp gcc_monitoring_deploy.tar.gz root@YOUR_DROPLET_IP:/tmp/
echo.
echo Then on your droplet:
echo   cd /tmp
echo   tar -xzf gcc_monitoring_deploy.tar.gz
echo   mv deployment /home/gcc/gcc_monitoring
echo   cd /home/gcc/gcc_monitoring
echo   bash deploy.sh
echo.
pause
