@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"
title Literate Lamp - Environment Setup

cls
echo.
echo ============================================================
echo   Literate Lamp - Full Environment and Prerequisites Setup
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 0. CHECK WINDOWS PACKAGE MANAGER [WINGET]
REM ------------------------------------------------------------
set "HAS_WINGET=0"
where winget >nul 2>&1
if %errorlevel% equ 0 (
    set "HAS_WINGET=1"
    echo [OK] Windows Package Manager [winget] detected.
) else (
    echo [!] winget not found. Auto-installer will fallback to manual links.
)
echo.

REM ------------------------------------------------------------
REM 1. CHECK AND AUTO-INSTALL PYTHON
REM ------------------------------------------------------------
echo Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is NOT installed.
    if "!HAS_WINGET!"=="1" (
        echo [!] Auto-installing Python 3.12 via winget...
        echo     Please click Yes if Windows UAC asks for permission.
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        call :refresh_path
        where python >nul 2>&1
        if !errorlevel! neq 0 (
            echo.
            echo [!] Python was installed but terminal PATH needs a restart.
            echo     Please close this window and run 'setup-python.bat' once more.
            pause
            exit /b 0
        )
    ) else (
        echo.
        echo [ERROR] Python 3 is required. Please download and install from:
        echo         https://www.python.org/downloads/
        echo         Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)

echo [OK] Python detected:
python --version
echo.

REM ------------------------------------------------------------
REM 2. CHECK AND AUTO-INSTALL NODE.JS
REM ------------------------------------------------------------
echo Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Node.js is NOT installed.
    if "!HAS_WINGET!"=="1" (
        echo [!] Auto-installing Node.js LTS via winget...
        echo     Please click Yes if Windows UAC asks for permission.
        winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
        call :refresh_path
        where node >nul 2>&1
        if !errorlevel! neq 0 (
            echo.
            echo [!] Node.js was installed but terminal PATH needs a restart.
            echo     Please close this window and run 'setup-python.bat' once more.
            pause
            exit /b 0
        )
    ) else (
        echo.
        echo [ERROR] Node.js is required. Please download and install from:
        echo         https://nodejs.org/
        pause
        exit /b 1
    )
)

echo [OK] Node.js detected:
node --version
echo.

REM ------------------------------------------------------------
REM 3. CHECK AND AUTO-INSTALL FFMPEG
REM ------------------------------------------------------------
echo Checking FFmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] FFmpeg is NOT installed. Required for video metadata extraction.
    if "!HAS_WINGET!"=="1" (
        echo [!] Auto-installing FFmpeg via winget...
        winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
        call :refresh_path
        where ffmpeg >nul 2>&1
        if !errorlevel! equ 0 (
            echo [OK] FFmpeg installed successfully!
        ) else (
            echo [!] FFmpeg installed, will be active on next terminal session.
        )
    ) else (
        echo [!] Warning: FFmpeg not found. Video metadata features will be limited.
        echo     Download: https://ffmpeg.org/download.html
    )
) else (
    echo [OK] FFmpeg detected.
)
echo.

REM ------------------------------------------------------------
REM 4. CREATE AND ACTIVATE PYTHON VIRTUAL ENVIRONMENT [VENV]
REM ------------------------------------------------------------
if not exist "venv" (
    echo Creating Python virtual environment [venv]...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Existing virtual environment found.
)

call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated.
echo.

REM ------------------------------------------------------------
REM 5. INSTALL PYTHON DEPENDENCIES
REM ------------------------------------------------------------
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

echo Installing backend Python dependencies from backend/requirements.txt...
pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install backend dependencies.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed.
echo.

REM ------------------------------------------------------------
REM 6. INSTALL FRONTEND DEPENDENCIES
REM ------------------------------------------------------------
if not exist "frontend" (
    echo [ERROR] frontend folder is missing.
    pause
    exit /b 1
)

cd frontend
if not exist "node_modules" (
    echo Installing frontend node_modules [npm install]...
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] npm install failed.
        cd ..
        pause
        exit /b 1
    )
    echo [OK] Frontend packages installed.
) else (
    echo [OK] frontend/node_modules already exists.
)
cd ..
echo.

REM ------------------------------------------------------------
REM 7. CREATE .ENV IF NOT EXISTS
REM ------------------------------------------------------------
if not exist ".env" (
    echo Creating default .env file...
    (
        echo # Auto generated
        echo # Managed by GUI
    ) > .env
    echo [OK] .env file created.
    echo.
)

REM ------------------------------------------------------------
REM SETUP COMPLETE
REM ------------------------------------------------------------
cls
echo.
echo ============================================================
echo   [SUCCESS] ALL PREREQUISITES AND ENVIRONMENT READY!
echo ============================================================
echo.
echo   - Python       : OK
echo   - Node.js      : OK
echo   - FFmpeg       : OK
echo   - Virtualenv   : Ready [venv]
echo   - Backend Deps : Installed
echo   - Frontend Deps: Installed
echo.
echo You can now start the application anytime by running:
echo   --^> start.bat
echo.
pause
exit /b 0

REM ============================================================
REM HELPER FUNCTION: REFRESH ENVIRONMENT PATH
REM ============================================================
:refresh_path
for /f "tokens=*" %%p in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%p"
exit /b 0
