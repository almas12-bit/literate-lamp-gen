@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

title Literate Lamp Launcher

cls
echo.
echo ============================================================
echo   Literate Lamp - Starting Application
echo ============================================================
echo.

REM ============================================================
REM CHECK AND VALIDATE VENV
REM ============================================================

set "VENV_OK=0"
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 (
        set "VENV_OK=1"
    )
)

if "!VENV_OK!"=="0" (
    echo [!] Virtual environment [venv] is missing or incompatible with this laptop.
    echo [!] Running setup-python.bat automatically to configure this machine...
    echo.
    call setup-python.bat
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Auto-setup failed. Please check the logs above.
        pause
        exit /b 1
    )
)

if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] Virtual environment belum berhasil dibuat.
    echo         Silakan jalankan setup-python.bat secara manual.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

echo [OK] Python environment ready
echo.

REM ============================================================
REM CREATE .ENV IF NOT EXISTS
REM ============================================================

if not exist ".env" (
    echo Creating .env...
    (
        echo # Auto generated
        echo # Managed by GUI
    ) > .env
    echo [OK] .env created
    echo.
)

REM ============================================================
REM CHECK NODE
REM ============================================================

where node >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Node.js not detected in PATH.
    echo [!] Running setup-python.bat to install prerequisites...
    call setup-python.bat
    if !errorlevel! neq 0 (
        echo [ERROR] Node.js is required. Download: https://nodejs.org/
        pause
        exit /b 1
    )
)

echo [OK] Node.js detected
echo.

REM ============================================================
REM INSTALL FRONTEND DEPENDENCIES
REM ============================================================

if not exist "frontend" (
    echo [ERROR] frontend folder missing
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
)

echo [OK] Frontend ready
echo.

REM ============================================================
REM START SERVICES (SINGLE TERMINAL MODE)
REM ============================================================

python launcher.py

if !errorlevel! neq 0 (
    echo.
    echo Application stopped.
    pause
)
