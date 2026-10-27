@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

cd /d "%~dp0"
title Literate Lamp Launcher

cls
echo.
echo ============================================================
echo   Literate Lamp - Memulai Aplikasi
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 1. AUTO-DETECT AND PREPEND STANDARD PATHS (NODE.JS)
REM ------------------------------------------------------------
if exist "%ProgramFiles%\nodejs" (
    set "PATH=%ProgramFiles%\nodejs;!PATH!"
)
if exist "%ProgramFiles(x86)%\nodejs" (
    set "PATH=%ProgramFiles(x86)%\nodejs;!PATH!"
)
if exist "%LOCALAPPDATA%\Programs\nodejs" (
    set "PATH=%LOCALAPPDATA%\Programs\nodejs;!PATH!"
)

REM ------------------------------------------------------------
REM 2. CHECK AND VALIDATE VIRTUAL ENVIRONMENT
REM ------------------------------------------------------------
set "VENV_READY=0"
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -c "import uvicorn, fastapi, httpx" >nul 2>&1
    if !errorlevel! equ 0 (
        set "VENV_READY=1"
    )
)

if "!VENV_READY!"=="0" (
    echo [i] Virtual environment [venv] belum siap atau dipindahkan dari laptop lain.
    echo [i] Menjalankan setup.bat secara otomatis...
    echo.
    call setup.bat
    if !errorlevel! neq 0 (
        echo.
        echo ============================================================
        echo [ERROR] Setup otomatis gagal. Silakan periksa pesan error di atas.
        echo ============================================================
        echo.
        pause
        exit /b 1
    )
)

if not exist "venv\Scripts\activate.bat" (
    echo.
    echo ============================================================
    echo [ERROR] Virtual environment belum berhasil dibuat.
    echo         Silakan klik ganda file setup.bat secara langsung.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo.
    echo ============================================================
    echo [ERROR] Gagal mengaktifkan virtual environment [venv].
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo [OK] Python virtual environment aktif.
echo.

REM ------------------------------------------------------------
REM 3. CREATE .ENV IF NOT EXISTS
REM ------------------------------------------------------------
if not exist ".env" (
    echo Menyiapkan file konfigurasi .env...
    (
        echo # Konfigurasi Literate Lamp
        echo # Dikelola otomatis oleh GUI
    ) > .env
    echo [OK] File .env siap.
    echo.
)

REM ------------------------------------------------------------
REM 4. CHECK NODE.JS
REM ------------------------------------------------------------
node -v >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Node.js belum terdeteksi di sistem.
    echo [!] Menjalankan setup.bat untuk instalasi...
    call setup.bat
    if !errorlevel! neq 0 (
        echo.
        echo ============================================================
        echo [ERROR] Node.js diperlukan tetapi belum terpasang.
        echo         Silakan download dari: https://nodejs.org/ [LTS]
        echo ============================================================
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Node.js siap:
node --version
echo.

REM ------------------------------------------------------------
REM 5. CHECK FRONTEND DEPENDENCIES
REM ------------------------------------------------------------
if not exist "frontend" (
    echo.
    echo ============================================================
    echo [ERROR] Folder frontend tidak ditemukan!
    echo ============================================================
    echo.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [!] Memasang dependensi frontend [npm install]...
    cd frontend
    call npm install
    if !errorlevel! neq 0 (
        echo.
        echo ============================================================
        echo [ERROR] Gagal memasang dependensi frontend.
        echo ============================================================
        cd ..
        echo.
        pause
        exit /b 1
    )
    cd ..
)

echo [OK] Frontend siap.
echo.

REM ------------------------------------------------------------
REM 6. LAUNCH APPLICATION (ALL-IN-ONE CONSOLE)
REM ------------------------------------------------------------
echo Menjalankan aplikasi Literate Lamp...
echo.

REM Gunakan python dari venv secara eksplisit agar bebas dari bentrok Microsoft Store
venv\Scripts\python.exe launcher.py

echo.
echo ============================================================
echo   Aplikasi Literate Lamp telah berhenti.
echo ============================================================
echo.
pause
