# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Base directories
ROOT_DIR = os.path.abspath(os.getcwd())
FRONTEND_DIST = os.path.join(ROOT_DIR, "frontend", "dist")

datas = []
if os.path.exists(FRONTEND_DIST):
    datas.append((FRONTEND_DIST, "dist"))

hiddenimports = [
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespans",
    "uvicorn.lifespans.on",
    "fastapi",
    "fastapi.staticfiles",
    "starlette",
    "starlette.middleware",
    "starlette.middleware.cors",
    "starlette.staticfiles",
    "pydantic",
    "httpx",
    "multipart",
    "python_multipart",
    "aiofiles",
    "dotenv",
    "config",
    "gemini_service",
    "queue_manager",
    "vector_service",
    "video_service",
    "main",
    "backend.config",
    "backend.gemini_service",
    "backend.queue_manager",
    "backend.vector_service",
    "backend.video_service",
    "backend.main",
]

a = Analysis(
    ['desktop_app.py'],
    pathex=[ROOT_DIR, os.path.join(ROOT_DIR, 'backend')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LiterateLamp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

