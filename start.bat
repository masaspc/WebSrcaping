@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
python main.py
if errorlevel 1 (
    echo.
    echo An error occurred.
    echo If you haven't run setup yet, please run setup.bat first.
    echo.
    pause
)
