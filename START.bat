@echo off
REM GCC Monitoring System - Quick Start Script
REM This script automatically activates the virtual environment and starts the app

echo.
echo ================================================
echo GCC Monitoring System - Quick Start
echo ================================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Error: Virtual environment not found!
    echo Please run setup.ps1 first to install the application.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the application
echo.
echo Starting GCC Monitoring System...
echo Open your browser and go to: http://localhost:8080
echo.
echo Default Login:
echo   Email: admin
echo   Password: 1931
echo.
echo Press Ctrl + C to stop the application
echo.

python app.py

pause
