@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo エラーが発生しました。
    echo まだセットアップしていない場合は、先に setup.bat を実行してください。
    echo.
    pause
)
