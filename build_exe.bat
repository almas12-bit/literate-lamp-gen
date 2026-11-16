@echo off
setlocal enabledelayedexpansion

echo ==============================================================
echo   Literate Lamp - Build Standalone Executable (.exe)
echo ==============================================================
echo.

:: 1. Check Python Venv
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv' tidak ditemukan.
    echo Silakan jalankan setup.bat terlebih dahulu.
    pause
    exit /b 1
)

:: 2. Check / Install PyInstaller
echo [1/3] Memeriksa PyInstaller...
.\venv\Scripts\python.exe -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [SYSTEM] Memasang PyInstaller di venv...
    .\venv\Scripts\python.exe -m pip install pyinstaller
)

:: 3. Build Frontend
echo [2/3] Membangun aset frontend (npm run build)...
call npm --prefix frontend run build
if %errorlevel% neq 0 (
    echo [ERROR] Gagal mem-build frontend.
    pause
    exit /b 1
)

:: 4. Build Executable via PyInstaller
echo [3/3] Meng-compile LiterateLamp.exe via PyInstaller...
.\venv\Scripts\python.exe -m PyInstaller literate_lamp.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller gagal melakukan compile.
    pause
    exit /b 1
)

echo.
echo ==============================================================
echo   BUILD BERHASIL!
echo   File executable: dist\LiterateLamp.exe
echo ==============================================================
echo.
pause

