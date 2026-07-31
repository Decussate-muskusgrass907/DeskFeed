@echo off
title DeskFeed Controller
cd /d "%~dp0"
"C:\Program Files\Python314\python.exe" app.py
if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to close.
    pause >nul
)
