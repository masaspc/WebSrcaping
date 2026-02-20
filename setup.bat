@echo off
chcp 65001 >nul 2>&1
title Webスクレイピングツール - セットアップ

echo ============================================
echo   Webスクレイピングツール 初回セットアップ
echo ============================================
echo.

cd /d "%~dp0"

REM --- Python確認 ---
echo [1/3] Pythonの確認...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo エラー: Pythonが見つかりません。
    echo https://www.python.org/downloads/ からPython 3.11以上をインストールしてください。
    echo インストール時に「Add Python to PATH」にチェックを入れてください。
    echo.
    pause
    exit /b 1
)
python --version
echo OK
echo.

REM --- パッケージインストール ---
echo [2/3] 必要なパッケージをインストール中...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo エラー: パッケージのインストールに失敗しました。
    echo ネットワーク接続を確認してください。
    pause
    exit /b 1
)
echo OK
echo.

REM --- フォルダ作成 ---
echo [3/3] フォルダを作成中...
if not exist "config" mkdir config
if not exist "output" mkdir output
if not exist "logs" mkdir logs
echo OK
echo.

echo ============================================
echo   セットアップ完了！
echo   start.bat をダブルクリックして起動できます。
echo ============================================
echo.
pause
