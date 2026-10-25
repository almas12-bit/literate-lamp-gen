@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

title Literate Lamp Launcher

cls
echo.
echo ============================================================
echo   Literate Lamp - Starting Application
echo ============================================================
echo.

REM ============================================================
REM CHECK VENV
REM ============================================================

if not exist "venv" (
    echo ERROR: venv not found
    echo Run setup-python.bat first
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if errorlevel 1 (
    echo Failed to activate venv
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

node -v >nul 2>&1

if errorlevel 1 (
    echo ERROR: Node.js not installed
    echo Download: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Node.js detected
echo.

REM ============================================================
REM INSTALL FRONTEND DEPENDENCIES
REM ============================================================

if not exist "frontend" (
    echo ERROR: frontend folder missing
    pause
    exit /b 1
)

cd frontend

if not exist "node_modules" (

    echo Installing frontend dependencies...
    echo.

    call npm install

    if errorlevel 1 (
        echo.
        echo Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
)

cd ..

echo [OK] Frontend ready
echo.

REM ============================================================
<<<<<<< HEAD
REM START SERVICES (SINGLE TERMINAL MODE)
REM ============================================================

python launcher.py

if errorlevel 1 (
    echo.
    echo Application stopped.
    pause
)
=======
REM START SERVICES
REM ============================================================

echo Starting backend...
start "Backend" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\activate.bat && python -m uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting frontend...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 2 /nobreak >nul

start http://localhost:5173

echo.
echo ============================================================
echo   Literate Lamp Running
echo ============================================================
echo.
echo Backend  : http://localhost:8000
echo Frontend : http://localhost:5173
echo.

pause
>>>>>>> 2731da004173e056ade5ccaf2f53ebf590c41c48
