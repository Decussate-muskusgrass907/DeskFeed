@echo off
chcp 65001 >nul
title DeskFeed Controller Builder

echo ========================================
echo  Building DeskFeed Controller EXE
echo ========================================
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found.
    exit /b 1
)

REM Create / use venv
if not exist venv (
    echo [1/4] Creating virtual environment...
    python -m venv venv
)
echo [1/4] Virtual environment ready

REM Install deps
echo [2/4] Installing dependencies...
.\venv\Scripts\pip install -q customtkinter pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip install failed.
    exit /b 1
)
echo [2/4] Dependencies installed

REM Build
echo [3/4] Building executable...
.\venv\Scripts\pyinstaller --noconsole --onefile --name "DeskFeed Controller" app.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)
echo [3/4] Build complete

echo.
echo ========================================
echo  SUCCESS! Executable created at:
echo  dist\DeskFeed Controller.exe
echo ========================================
pause
