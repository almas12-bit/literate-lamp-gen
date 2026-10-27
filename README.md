
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

## Gemini API Keys

Get free keys at: https://aistudio.google.com/app/apikey

Free tier limits:
- 2.5 Flash: 10 req/min, 500 req/day
- 2.0 Flash: 15 req/min, 1500 req/day
- 2.5 Flash Lite: 30 req/min (fastest for bulk)
