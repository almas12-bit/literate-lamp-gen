@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

cd /d "%~dp0"
title Literate Lamp - Setup Otomatis

echo.
echo ============================================================
echo   Literate Lamp - Setup Otomatis Semua Dependensi
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 0. PREPEND STANDARD SYSTEM DIRECTORIES TO PATH
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
if exist "%ProgramFiles%\GhostTrap\bin" (
    set "PATH=%ProgramFiles%\GhostTrap\bin;!PATH!"
)
if exist "%ProgramFiles(x86)\GhostTrap\bin" (
    set "PATH=%ProgramFiles(x86)\GhostTrap\bin;!PATH!"
)
for /d %%G in ("%ProgramFiles%\gs\gs*") do (
    if exist "%%G\bin\gswin64c.exe" set "PATH=%%G\bin;!PATH!"
    if exist "%%G\bin\gsc.exe" set "PATH=%%G\bin;!PATH!"
)
for /d %%G in ("%ProgramFiles(x86)%\gs\gs*") do (
    if exist "%%G\bin\gswin32c.exe" set "PATH=%%G\bin;!PATH!"
    if exist "%%G\bin\gsc.exe" set "PATH=%%G\bin;!PATH!"
)

set "HAS_WINGET=0"
where winget >nul 2>&1
if !errorlevel! equ 0 (
    set "HAS_WINGET=1"
    echo [OK] Windows Package Manager [winget] terdeteksi.
) else (
    echo [i] winget tidak ditemukan. Beberapa komponen mungkin perlu diinstal manual.
)
echo.

REM ------------------------------------------------------------
REM 1. CHECK AND DETECT PYTHON
REM ------------------------------------------------------------
echo [1/7] Memeriksa instalasi Python...
set "PYTHON_EXEC="

REM Uji perintah 'python' bawaan PATH
python -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXEC=python"
    goto :python_detected
)

REM Uji Python Launcher 'py'
py -3 -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXEC=py -3"
    goto :python_detected
)

REM Uji lokasi instalasi standar Python di Windows
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist "%%~p" (
        "%%~p" -c "import sys" >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_EXEC=%%~p"
            goto :python_detected
        )
    )
)

REM Jika Python tidak ditemukan sama sekali
echo [!] Python 3 belum terpasang atau terhalang alias Microsoft Store.
if "!HAS_WINGET!"=="1" (
    echo [!] Menginstall Python 3.12 secara otomatis via winget...
    echo     CATATAN: Jika muncul pop-up Windows UAC izin administrator, silakan klik 'YES' / 'YA'.
    winget install Python.Python.3.12 --override "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1" --accept-package-agreements --accept-source-agreements --disable-interactivity
    call :refresh_path

    python -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXEC=python"
        goto :python_detected
    )
    for %%p in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%ProgramFiles%\Python312\python.exe"
        "C:\Python312\python.exe"
    ) do (
        if exist "%%~p" (
            set "PYTHON_EXEC=%%~p"
            goto :python_detected
        )
    )
    echo.
    echo [!] Python berhasil dipasang, tetapi Windows membutuhkan jendela baru untuk memuat PATH.
    echo     Silakan tutup jendela ini lalu klik ganda setup.bat lagi.
    echo.
    pause
    exit /b 0
)

echo.
echo ============================================================
echo [ERROR] Python 3 belum terpasang di laptop ini!
echo ============================================================
echo.
echo Panduan instalasi cepat:
echo 1. Buka browser: https://www.python.org/downloads/
echo 2. Download installer Python [disarankan versi 3.11 atau 3.12]
echo 3. SANGAT PENTING: Centang kotak 'Add Python to PATH' di layar awal installer!
echo 4. Jalankan kembali setup.bat setelah instalasi selesai.
echo.
pause
exit /b 1

:python_detected
echo [OK] Python siap digunakan:
if "!PYTHON_EXEC!"=="python" (
    python --version
) else if "!PYTHON_EXEC!"=="py -3" (
    py -3 --version
) else (
    "!PYTHON_EXEC!" --version
)
echo.

REM ------------------------------------------------------------
REM 2. CHECK AND DETECT NODE.JS
REM ------------------------------------------------------------
echo [2/7] Memeriksa Node.js...
node -v >nul 2>&1
if !errorlevel! equ 0 goto :nodejs_detected

if exist "%ProgramFiles%\nodejs\node.exe" (
    set "PATH=%ProgramFiles%\nodejs;!PATH!"
)
if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\nodejs;!PATH!"
)

node -v >nul 2>&1
if !errorlevel! equ 0 goto :nodejs_detected

echo [!] Node.js belum terdeteksi di laptop ini.
if "!HAS_WINGET!"=="1" (
    echo.
    echo [INFO] Sedang mencoba memasang Node.js LTS otomatis via winget...
    echo        PERHATIAN: Jika muncul jendela izin Windows [UAC], silakan klik 'YES' / 'YA'.
    echo        Proses unduh dan instalasi biasanya memakan waktu 1-2 menit.
    echo.
    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --disable-interactivity
    call :refresh_path

    node -v >nul 2>&1
    if !errorlevel! equ 0 goto :nodejs_detected

    if exist "%ProgramFiles%\nodejs\node.exe" (
        set "PATH=%ProgramFiles%\nodejs;!PATH!"
        goto :nodejs_detected
    )

    echo.
    echo [i] Node.js telah selesai diinstal via winget.
    echo     Terminal perlu ditutup dan dibuka kembali agar PATH Node.js aktif.
    echo     Silakan tutup jendela ini, lalu jalankan setup.bat sekali lagi.
    echo.
    pause
    exit /b 0
)

echo.
echo ============================================================
echo [PERHATIAN] Node.js diperlukan untuk menjalankan tampilan antarmuka web.
echo ============================================================
echo.
echo Silakan download dan pasang Node.js LTS secara manual:
echo 1. Kunjungi: https://nodejs.org/
echo 2. Download dan install versi LTS [klik Next sampai selesai].
echo 3. Setelah selesai, jalankan kembali setup.bat.
echo.
pause
exit /b 1

:nodejs_detected
echo [OK] Node.js siap:
node --version
echo.

REM ------------------------------------------------------------
REM 3. CHECK FFMPEG (AUTO-INSTALL VIA WINGET)
REM ------------------------------------------------------------
echo [3/7] Memeriksa FFmpeg [diperlukan untuk analisis video]...
ffmpeg -version >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] FFmpeg siap.
    goto :ffmpeg_done
)

echo [i] FFmpeg belum terpasang.
if "!HAS_WINGET!"=="1" (
    echo     Mencoba memasang FFmpeg via winget...
    winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements --disable-interactivity >nul 2>&1
    call :refresh_path
    ffmpeg -version >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] FFmpeg berhasil dipasang.
    ) else (
        echo [i] FFmpeg akan aktif setelah jendela ini ditutup dan dibuka kembali.
        echo [i] Atau download manual: https://ffmpeg.org/download.html
    )
) else (
    echo [i] FFmpeg dapat dipasang manual: https://ffmpeg.org/download.html
)

:ffmpeg_done
echo.

REM ------------------------------------------------------------
REM 4. CHECK GHOSTSCRIPT (AUTO-INSTALL VIA WINGET / OFFICIAL)
REM    Diperlukan untuk membaca file .ai dan .eps
REM ------------------------------------------------------------
echo [4/7] Memeriksa Ghostscript [diperlukan untuk file .ai dan .eps]...
set "GS_OK=0"

gsc -v >nul 2>&1
if !errorlevel! equ 0 ( set "GS_OK=1" & goto :gs_found )
gswin64c -v >nul 2>&1
if !errorlevel! equ 0 ( set "GS_OK=1" & goto :gs_found )
gswin32c -v >nul 2>&1
if !errorlevel! equ 0 ( set "GS_OK=1" & goto :gs_found )
gs -v >nul 2>&1
if !errorlevel! equ 0 ( set "GS_OK=1" & goto :gs_found )

REM Cari di lokasi default GhostTrap dan Ghostscript
if exist "%ProgramFiles%\GhostTrap\bin\gsc.exe" (
    set "PATH=%ProgramFiles%\GhostTrap\bin;!PATH!"
    set "GS_OK=1"
    goto :gs_found
)
if exist "%ProgramFiles(x86)%\GhostTrap\bin\gsc.exe" (
    set "PATH=%ProgramFiles(x86)%\GhostTrap\bin;!PATH!"
    set "GS_OK=1"
    goto :gs_found
)
for /d %%G in ("%ProgramFiles%\gs\gs*") do (
    if exist "%%G\bin\gswin64c.exe" (
        set "PATH=%%G\bin;!PATH!"
        set "GS_OK=1"
        goto :gs_found
    )
    if exist "%%G\bin\gsc.exe" (
        set "PATH=%%G\bin;!PATH!"
        set "GS_OK=1"
        goto :gs_found
    )
)
for /d %%G in ("%ProgramFiles(x86)%\gs\gs*") do (
    if exist "%%G\bin\gswin32c.exe" (
        set "PATH=%%G\bin;!PATH!"
        set "GS_OK=1"
        goto :gs_found
    )
)

:gs_found
if "!GS_OK!"=="1" (
    echo [OK] Ghostscript siap.
    goto :gs_done
)

echo [i] Ghostscript belum terpasang.
if "!HAS_WINGET!"=="1" (
    echo [INFO] Mengunduh dan memasang Ghostscript otomatis via winget...
    echo        [Proses ini memakan waktu sekitar 1 menit, mohon tunggu]...
    winget install PaperCutSoftware.GhostTrap --accept-package-agreements --accept-source-agreements --disable-interactivity >nul 2>&1
    call :refresh_path

    if exist "%ProgramFiles%\GhostTrap\bin\gsc.exe" (
        set "PATH=%ProgramFiles%\GhostTrap\bin;!PATH!"
        set "GS_OK=1"
    )
    if exist "%ProgramFiles(x86)%\GhostTrap\bin\gsc.exe" (
        set "PATH=%ProgramFiles(x86)%\GhostTrap\bin;!PATH!"
        set "GS_OK=1"
    )
    gsc -v >nul 2>&1
    if !errorlevel! equ 0 set "GS_OK=1"
)

if "!GS_OK!"=="1" (
    echo [OK] Ghostscript berhasil dipasang secara otomatis.
) else (
    echo.
    echo [!] Ghostscript belum terpasang otomatis.
    echo     Anda dapat mengunduhnya secara manual jika memerlukan file .ai dan .eps:
    echo     https://ghostscript.com/releases/gsdnld.html
    echo.
)

:gs_done
echo.

REM ------------------------------------------------------------
REM 5. CREATE / VALIDATE VIRTUAL ENVIRONMENT [VENV]
REM ------------------------------------------------------------
echo [5/7] Menyiapkan Python Virtual Environment [venv]...
set "NEED_NEW_VENV=0"

if not exist "venv" goto :create_new_venv
if not exist "venv\Scripts\python.exe" goto :corrupt_venv
if not exist "venv\Scripts\activate.bat" goto :corrupt_venv

REM Uji apakah venv lama cocok dengan laptop ini atau hasil copy laptop lain
"venv\Scripts\python.exe" -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Virtual environment [venv] yang ada valid dan kompatibel dengan laptop ini.
    goto :activate_existing_venv
)

:corrupt_venv
echo [!] Virtual environment lama tidak kompatibel [mungkin hasil salin dari laptop lain].
echo     Sedang membersihkan venv lama...
set "NEED_NEW_VENV=1"

:create_new_venv
if exist "venv" (
    rmdir /s /q venv >nul 2>&1
)

echo.
echo [INFO] Sedang membuat Virtual Environment [venv] baru...
echo        [Proses ini memakan waktu sekitar 15-30 detik, mohon tunggu]...
echo.

if "!PYTHON_EXEC!"=="py -3" (
    py -3 -m venv venv
) else if "!PYTHON_EXEC!"=="python" (
    python -m venv venv
) else (
    "!PYTHON_EXEC!" -m venv venv
)

if !errorlevel! neq 0 (
    echo.
    echo ============================================================
    echo [ERROR] Pembuatan venv gagal!
    echo ============================================================
    echo Pastikan instalasi Python memiliki modul standard venv.
    echo.
    pause
    exit /b 1
)
echo [OK] Virtual environment baru berhasil dibuat.

:activate_existing_venv
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [ERROR] File venv\Scripts\activate.bat tidak ditemukan!
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Gagal mengaktifkan virtual environment.
    echo.
    pause
    exit /b 1
)
echo [OK] Virtual environment aktif.
echo.

REM ------------------------------------------------------------
REM 6. INSTALL BACKEND DEPENDENCIES
REM ------------------------------------------------------------
echo [6/7] Memasang dependensi Python backend...
echo [INFO] Mengunduh dan memasang paket backend [FastAPI, Uvicorn, HTTPX]...
echo        [Proses ini menggunakan koneksi internet, mohon tunggu]...
echo.

python -m pip install -r backend\requirements.txt
if !errorlevel! neq 0 (
    echo.
    echo ============================================================
    echo [ERROR] Gagal memasang paket Python backend!
    echo ============================================================
    echo Pastikan laptop terhubung ke internet.
    echo.
    pause
    exit /b 1
)
echo.
echo [OK] Paket Python backend terpasang lengkap.
echo.

REM ------------------------------------------------------------
REM 7. INSTALL FRONTEND DEPENDENCIES
REM ------------------------------------------------------------
echo [7/7] Memeriksa dependensi antarmuka frontend...
if not exist "frontend" (
    echo [ERROR] Folder frontend tidak ditemukan!
    pause
    exit /b 1
)

cd frontend
if not exist "node_modules" (
    echo.
    echo [INFO] Folder node_modules belum ada.
    echo        Memasang paket frontend via npm install [mohon tunggu 1-2 menit]...
    echo.
    call npm install
    if !errorlevel! neq 0 (
        echo.
        echo ============================================================
        echo [ERROR] npm install gagal!
        echo ============================================================
        cd ..
        pause
        exit /b 1
    )
    echo [OK] Dependensi frontend berhasil dipasang.
) else (
    echo [OK] Folder frontend\node_modules sudah tersedia.
)
cd ..
echo.

REM ------------------------------------------------------------
REM CREATE .ENV IF NOT EXISTS
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
REM SELESAI
REM ------------------------------------------------------------
echo.
echo ============================================================
echo   [SUKSES] SEMUA SETUP DAN DEPENDENSI TELAH SIAP!
echo ============================================================
echo.
echo   - Python             : Siap
echo   - Node.js            : Siap
echo   - FFmpeg             : Siap [analisis video]

REM Cek status GS final untuk summary yang akurat
set "GS_FINAL=0"
gsc -v >nul 2>&1
if !errorlevel! equ 0 set "GS_FINAL=1"
gswin64c -v >nul 2>&1
if !errorlevel! equ 0 set "GS_FINAL=1"
gswin32c -v >nul 2>&1
if !errorlevel! equ 0 set "GS_FINAL=1"
gs -v >nul 2>&1
if !errorlevel! equ 0 set "GS_FINAL=1"
if exist "%ProgramFiles%\GhostTrap\bin\gsc.exe" set "GS_FINAL=1"
if exist "%ProgramFiles(x86)%\GhostTrap\bin\gsc.exe" set "GS_FINAL=1"
for /d %%G in ("%ProgramFiles%\gs\gs*") do (
    if exist "%%G\bin\gswin64c.exe" set "GS_FINAL=1"
    if exist "%%G\bin\gsc.exe" set "GS_FINAL=1"
)
for /d %%G in ("%ProgramFiles(x86)%\gs\gs*") do (
    if exist "%%G\bin\gswin32c.exe" set "GS_FINAL=1"
    if exist "%%G\bin\gsc.exe" set "GS_FINAL=1"
)

if "!GS_FINAL!"=="1" (
    echo   - Ghostscript        : Siap [analisis .ai dan .eps]
) else (
    echo   - Ghostscript        : BELUM SIAP - install manual: https://ghostscript.com/releases/gsdnld.html
    echo                          File .ai dan .eps tidak bisa diproses sampai Ghostscript terinstall.
)

echo   - Virtual Environment: Aktif [venv khusus laptop ini]
echo   - Backend Packages   : Terinstall
echo   - Frontend Packages  : Terinstall
echo.
echo Sekarang Anda dapat menjalankan aplikasi kapan saja dengan:
echo   --^> Klik ganda file: start.bat
echo.
pause
exit /b 0

REM ============================================================
REM HELPER FUNCTION: REFRESH PATH
REM ============================================================
:refresh_path
if exist "%ProgramFiles%\nodejs" set "PATH=%ProgramFiles%\nodejs;!PATH!"
if exist "%ProgramFiles(x86)%\nodejs" set "PATH=%ProgramFiles(x86)%\nodejs;!PATH!"
if exist "%LOCALAPPDATA%\Programs\nodejs" set "PATH=%LOCALAPPDATA%\Programs\nodejs;!PATH!"
if exist "%ProgramFiles%\GhostTrap\bin" set "PATH=%ProgramFiles%\GhostTrap\bin;!PATH!"
if exist "%ProgramFiles(x86)\GhostTrap\bin" set "PATH=%ProgramFiles(x86)\GhostTrap\bin;!PATH!"
for /d %%G in ("%ProgramFiles%\gs\gs*") do (
    if exist "%%G\bin\gswin64c.exe" set "PATH=%%G\bin;!PATH!"
    if exist "%%G\bin\gsc.exe" set "PATH=%%G\bin;!PATH!"
)
for /d %%G in ("%ProgramFiles(x86)%\gs\gs*") do (
    if exist "%%G\bin\gswin32c.exe" set "PATH=%%G\bin;!PATH!"
    if exist "%%G\bin\gsc.exe" set "PATH=%%G\bin;!PATH!"
)
exit /b 0

