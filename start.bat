@echo off
chcp 65001 >nul
title Sinyuk Imagen

echo ========================================
echo   Sinyuk Imagen - Starting...
echo ========================================
echo.

:: Check if .env exists
if not exist .env (
    if exist .env.example (
        echo [INFO] .env not found, copying from .env.example...
        copy .env.example .env >nul
        echo [WARN] Please edit .env and fill in your API keys, then re-run this script.
        pause
        exit /b 1
    )
)

:: Create venv if not exists
if not exist .venv\Scripts\activate.bat (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate venv
call .venv\Scripts\activate.bat

:: Install dependencies
echo [INFO] Checking dependencies...
python -m pip install -r requirements.txt -q

:: Launch app
echo.
echo [INFO] Launching app...
echo.
python app.py

pause
