@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cls
echo.
echo ════════════════════════════════════════════════════════════
echo   Literate Lamp - Setup Python Virtual Environment
echo ════════════════════════════════════════════════════════════
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    cls
    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║                      ERROR                                 ║
    echo ║               Python 3 NOT FOUND on System                 ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.
    echo Please download and install Python from:
    echo    https://www.python.org/downloads/
    echo.
    echo   IMPORTANT: During installation, CHECK the box:
    echo    "Add Python to PATH"
    echo.
    echo Then restart this script.
    echo.
    pause
    exit /b 1
)

echo ✓ Python found: 
python --version
echo.

REM Check if venv already exists
if exist "venv" (
    echo ✓ Virtual environment already exists
    echo   Activating existing venv...
    call venv\Scripts\activate.bat
) else (
    echo  Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
    echo.
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo ✓ Virtual environment activated
echo.

echo Upgrading pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo  Warning: pip upgrade failed (non-critical)
)

echo ✓ Pip upgraded
echo.

echo Installing Python dependencies from backend/requirements.txt...
pip install -r backend/requirements.txt
if %errorlevel% neq 0 (
    echo  Failed to install Python dependencies
    pause
    exit /b 1
)

echo ✓ Python dependencies installed
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    cls
    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║                      WARNING                              ║
    echo ║              Node.js NOT FOUND on System                  ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.
    echo Please download and install Node.js from:
    echo    https://nodejs.org/ (LTS version recommended)
    echo.
    echo Then restart this script.
    echo.
    pause
    exit /b 1
)

echo ✓ Node.js found:
node --version
echo.

echo  Installing frontend dependencies...
cd frontend
if not exist "node_modules" (
    call npm install
    if %errorlevel% neq 0 (
        echo  Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
) else (
    echo ✓ node_modules already exists, skipping npm install
)
cd ..

echo ✓ Frontend dependencies installed
echo.

cls
echo.
echo ════════════════════════════════════════════════════════════
echo   ✓ SETUP COMPLETE!
echo ════════════════════════════════════════════════════════════
echo.
echo Next steps:
echo   1. Edit .env file and add your API keys
echo   2. Run 'start.bat' to start the application
echo.
echo Documentation: Open README.md
echo.
pause
