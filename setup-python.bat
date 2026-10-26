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
if !errorlevel! equ 0 (
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
set "PYTHON_EXEC="

REM Test if 'python' works and is not the Microsoft Store dummy shortcut
python -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXEC=python"
) else (
    REM Check Python Launcher 'py'
    py -3 -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXEC=py -3"
    ) else (
        REM Search standard install directories if PATH was not set
        for %%d in (
            "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
            "%ProgramFiles%\Python313\python.exe"
            "%ProgramFiles%\Python312\python.exe"
            "%ProgramFiles%\Python311\python.exe"
            "C:\Python314\python.exe"
            "C:\Python313\python.exe"
            "C:\Python312\python.exe"
            "C:\Python311\python.exe"
        ) do (
            if not defined PYTHON_EXEC (
                if exist %%d (
                    %%d -c "import sys" >nul 2>&1
                    if !errorlevel! equ 0 (
                        set "PYTHON_EXEC=%%~d"
                    )
                )
            )
        )
    )
)

if not defined PYTHON_EXEC (
    echo [!] Python is NOT installed (or only Microsoft Store dummy shortcut was found).
    if "!HAS_WINGET!"=="1" (
        echo [!] Auto-installing Python 3.12 via winget...
        echo     Please click Yes if Windows UAC asks for permission.
        winget install Python.Python.3.12 --override "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1" --accept-package-agreements --accept-source-agreements
        call :refresh_path
        
        REM Test again after winget install
        python -c "import sys" >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_EXEC=python"
        ) else (
            for %%d in (
                "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
                "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
                "%ProgramFiles%\Python312\python.exe"
                "C:\Python312\python.exe"
            ) do (
                if not defined PYTHON_EXEC (
                    if exist %%d set "PYTHON_EXEC=%%~d"
                )
            )
        )
        
        if not defined PYTHON_EXEC (
            echo.
            echo [!] Python was installed but Windows requires a fresh terminal to load PATH.
            echo     Please close this window and double-click 'setup-python.bat' again.
            pause
            exit /b 0
        )
    ) else (
        echo.
        echo ============================================================
        echo [ERROR] Python 3 belum terinstall di laptop ini!
        echo ============================================================
        echo Windows menampilkan pesan Microsoft Store karena Python resmi
        echo belum dipasang atau belum dicentang "Add Python to PATH".
        echo.
        echo Cara instalasi mudah:
        echo 1. Kunjungi: https://www.python.org/downloads/
        echo 2. Download installer Python terbaru untuk Windows.
        echo 3. SAAT INSTALL: PENTING centang kotak "Add Python to PATH" di bagian bawah!
        echo 4. Jalankan kembali setup-python.bat setelah instalasi selesai.
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Python functional:
!PYTHON_EXEC! --version
echo.

REM ------------------------------------------------------------
REM 2. CHECK AND AUTO-INSTALL NODE.JS
REM ------------------------------------------------------------
echo Checking Node.js...
node -v >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Node.js is NOT installed.
    if "!HAS_WINGET!"=="1" (
        echo [!] Auto-installing Node.js LTS via winget...
        echo     Please click Yes if Windows UAC asks for permission.
        winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
        call :refresh_path
        node -v >nul 2>&1
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
ffmpeg -version >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] FFmpeg is NOT installed. Required for video metadata extraction.
    if "!HAS_WINGET!"=="1" (
        echo [!] Auto-installing FFmpeg via winget...
        winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
        call :refresh_path
        ffmpeg -version >nul 2>&1
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
set "REBUILD_VENV=0"

if exist "venv" (
    echo Validating existing virtual environment [venv]...
    if exist "venv\Scripts\python.exe" (
        "venv\Scripts\python.exe" -c "import sys" >nul 2>&1
        if !errorlevel! neq 0 (
            echo [!] Existing venv is invalid or was copied from another laptop.
            echo     (Hardcoded paths pointing to previous machine detected)
            set "REBUILD_VENV=1"
        ) else (
            echo [OK] Existing virtual environment verified and working.
        )
    ) else (
        echo [!] Virtual environment exists but is incomplete.
        set "REBUILD_VENV=1"
    )
) else (
    set "REBUILD_VENV=1"
)

if "!REBUILD_VENV!"=="1" (
    if exist "venv" (
        echo [!] Removing incompatible virtual environment...
        rmdir /s /q venv >nul 2>&1
    )
    echo Creating fresh Python virtual environment [venv] for this laptop...
    !PYTHON_EXEC! -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create venv.
        echo         Pastikan Python terinstall dengan benar dan bukan shortcut Microsoft Store.
        pause
        exit /b 1
    )
    echo [OK] Fresh virtual environment created successfully.
)

if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] venv\Scripts\activate.bat tidak ditemukan.
    echo         Pembuatan virtual environment gagal.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Failed to activate venv.
    echo         Please ensure Python is added to your PATH and restart your terminal.
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
if !errorlevel! neq 0 (
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
