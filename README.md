
Auto-generate metadata (description, keywords, categories) using Google Gemini AI.

## Features
- Image, video, **vector (.ai, .eps)** support
- Multiple Gemini models (2.5 Pro, 2.5 Flash, 2.5 Flash Lite, 2.0 Flash, 2.0 Flash Lite)
- Multi API key with auto-rolling on rate limit
- Start / Pause / Stop queue controls
- Export CSV for bulk upload
- FFmpeg-based video frame extraction
- Ghostscript-based .ai / .eps vector conversion

---

## Requirements

- Python 3.10+
- Node.js 18+
- FFmpeg (for video support)
- Ghostscript (for .ai and .eps support)

> **Windows users:** All dependencies are installed automatically by `setup.bat`

### Install FFmpeg (manual)

**Windows:**
```
winget install Gyan.FFmpeg
```
or download from https://ffmpeg.org/download.html and add to PATH

**macOS:**
```
brew install ffmpeg
```

**Ubuntu/Debian:**
```
sudo apt install ffmpeg
```

### Install Ghostscript (manual)

**Windows:**
```
winget install ArtifexSoftware.GhostScript
```
or download from https://ghostscript.com/releases/gsdnld.html and add to PATH

**macOS:**
```
brew install ghostscript
```

**Ubuntu/Debian:**
```
sudo apt install ghostscript
```

---

## Setup & Run

### Windows (Otomatis)

1. Klik ganda **`setup.bat`** — menginstall semua dependensi secara otomatis
2. Klik ganda **`start.bat`** — menjalankan aplikasi

```
setup.bat   ← jalankan sekali untuk setup
start.bat   ← jalankan setiap kali ingin membuka aplikasi
```

### Linux / macOS

```bash
bash setup-python.sh
bash start.sh
```

Frontend runs at: http://localhost:5173
Backend runs at: http://localhost:8000

## Usage

1. Open http://localhost:5173
2. Click **API KEYS** → paste your Gemini API keys (one per line) → **SAVE KEYS**
3. Select a **Gemini model** from the dropdown
4. Drag & drop images / videos / .ai / .eps onto the drop zone
5. Click **START** to begin analysis
6. Edit description/keywords/categories if needed
7. Click **EXPORT CSV** to download
8. When there are any errors of shutterstock csv, just select none at shutterstock categories

---

## API Key Rolling

When a key hits rate limit (429), the backend automatically:
1. Marks that key as `rate_limited`
2. Switches to the next available key
3. Auto-resets the key after ~65 seconds
4. Shows live key status in the UI (green/yellow/red)

---

---

## Standalone Executable (.exe) & GitHub Releases

Aplikasi Literate Lamp dapat diunduh sebagai paket `.exe` mandiri tanpa perlu memasang Python, Node.js, FFmpeg, atau Ghostscript secara manual.

### Cara Menggunakan Versi Release:
1. Unduh file `LiterateLamp-vX.Y.Z-Windows-x64.zip` dari halaman [Releases di GitHub](https://github.com/almas12-bit/literate-lamp-gen/releases).
2. Ekstrak seluruh isi file ZIP ke folder komputer Anda.
3. Klik ganda **`LiterateLamp.exe`**.
4. Browser akan otomatis terbuka di `http://localhost:8000`.

### Cara Membuat Rilis Baru via GitHub Actions:
Proses kompilasi dan pembuatan rilis diotomatisasi menggunakan GitHub Actions workflow (`.github/workflows/build-release.yml`).

Setiap kali ada perubahan/versi baru, buat git tag dan push ke GitHub:
```bash
git add .
git commit -m "feat: rilis pembaruan versi v2.0.0"
git tag v2.0.0
git push origin main --tags
```
GitHub Actions akan otomatis:
1. Mem-build frontend React (`npm run build`).
2. Mengunduh FFmpeg & Ghostscript portabel ke folder `bin/`.
3. Meng-compile file `LiterateLamp.exe` menggunakan PyInstaller.
4. Mengemas seluruh paket ke dalam file ZIP.
5. Menerbitkan rilis resmi baru di tab **Releases** GitHub secara otomatis.

*(Anda juga dapat memicu build rilis secara manual dari menu **Actions** -> **Build & Release Standalone Executable** -> **Run workflow** di web GitHub).*

### Build Executable di Komputer Lokal:
Jika ingin meng-compile file `.exe` sendiri di komputer lokal:
```cmd
build_exe.bat
```
File executable yang dihasilkan akan berada di folder `dist\LiterateLamp.exe`.

