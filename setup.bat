@echo off
title Web Scraping Tool - Setup

echo ============================================
echo   Web Scraping Tool - Initial Setup
echo ============================================
echo.

cd /d "%~dp0"

REM --- Python Check ---
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found.
    echo Please install Python 3.11 or later from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
python --version
echo OK
echo.

REM --- Install packages ---
echo [2/3] Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Package installation failed.
    echo Please check your network connection.
    pause
    exit /b 1
)
echo OK
echo.

REM --- Create folders ---
echo [3/3] Creating folders...
if not exist "config" mkdir config
if not exist "output" mkdir output
if not exist "logs" mkdir logs
echo OK
echo.

echo ============================================
echo   Setup complete!
echo   Double-click start.bat to launch the app.
echo ============================================
echo.
pause
