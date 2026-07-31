@echo off
REM Install Laptop Agent as a Windows Background Service
REM Requires: Python 3.10+, pip

echo ========================================
echo  DeskFeed Agent - Windows Service Installer
echo ========================================
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Please install Python 3.10+ first.
    exit /b 1
)

REM Create virtual environment
echo [1/4] Creating virtual environment...
if not exist venv (
    python -m venv venv
)

REM Activate and install deps
echo [2/4] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip install failed.
    exit /b 1
)

REM Install as Windows service using NSSM if available, else use task scheduler
echo [3/4] Checking for NSSM...
where nssm >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Installing with NSSM...
    nssm install LaptopAgent "%~dp0venv\Scripts\python.exe" "%~dp0main.py"
    nssm set LaptopAgent AppDirectory "%~dp0"
    nssm set LaptopAgent Start SERVICE_AUTO_START
    nssm set LaptopAgent AppStdout "%~dp0logs\service.log"
    nssm set LaptopAgent AppStderr "%~dp0logs\error.log"
    nssm start LaptopAgent
) else (
    echo NSSM not found. Creating scheduled task instead...
    schtasks /create /tn "LaptopAgent" /tr "%~dp0venv\Scripts\python.exe %~dp0main.py" /sc onlogon /ru "%USERNAME%" /f /it
    echo Scheduled task created. It will run at next logon.
)

echo.
echo [4/4] Installation complete!
echo.
echo Next steps:
echo 1. Copy .env.example to .env and configure your server URL
echo 2. Run main.py manually first to register the device:
echo    .\venv\Scripts\python main.py
echo 3. Note the Device ID and Pairing PIN shown in the console
echo 4. Use those credentials in the Android app
echo.
pause
