import asyncio
import subprocess
import tempfile
import os
import glob
import shutil
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)

# Common Ghostscript executable names to probe via PATH
_GS_CANDIDATES = ["gsc", "gswin64c", "gswin32c", "gs"]

# Common Windows installation directories for Ghostscript / GhostTrap
_GS_WIN_DIRS = [
    r"C:\Program Files\GhostTrap\bin",
    r"C:\Program Files (x86)\GhostTrap\bin",
    r"C:\Program Files\gs",
    r"C:\Program Files (x86)\gs",
]


def find_ghostscript() -> Optional[str]:
    """
    Find Ghostscript executable.
    1. Check PATH first (gsc, gswin64c, gswin32c, gs)
    2. Fall back to scanning common Windows install directories (GhostTrap, gs)
    """
    # 1. Check PATH
    for name in _GS_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path

    # 2. Check direct bin folders (e.g. GhostTrap\bin)
    for base in [r"C:\Program Files\GhostTrap\bin", r"C:\Program Files (x86)\GhostTrap\bin"]:
        for exe in ("gsc.exe", "gswin64c.exe", "gswin32c.exe", "gs.exe"):
            candidate = os.path.join(base, exe)
            if os.path.isfile(candidate):
                return candidate

    # 3. Scan versioned dirs (e.g. C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe)
    for base in [r"C:\Program Files\gs", r"C:\Program Files (x86)\gs"]:
        if not os.path.isdir(base):
            continue
        for versioned in sorted(glob.glob(os.path.join(base, "gs*")), reverse=True):
            for exe in ("gsc.exe", "gswin64c.exe", "gswin32c.exe", "gs.exe"):
                candidate = os.path.join(versioned, "bin", exe)
                if os.path.isfile(candidate):
                    return candidate

    return None


def check_ghostscript_sync() -> bool:
    """Return True if Ghostscript is available."""
    gs = find_ghostscript()
    if not gs:
        return False
    try:
        result = subprocess.run(
            [gs, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


async def check_ghostscript() -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, check_ghostscript_sync)


def convert_vector_to_png_sync(file_data: bytes, ext: str = ".eps") -> Optional[bytes]:
    """
    Convert an .ai or .eps file to PNG bytes using Ghostscript.
    Returns PNG bytes on success, or None on failure.
    """
    gs = find_ghostscript()
    if not gs:
        logger.error(
            "Ghostscript not found. Install from https://ghostscript.com/releases/gsdnld.html "
            "and make sure it is on your system PATH."
        )
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, f"input{ext}")
        output_path = os.path.join(tmpdir, "output.png")

        with open(input_path, "wb") as f:
            f.write(file_data)

        cmd = [
            gs,
            "-dNOPAUSE",
            "-dBATCH",
            "-dSAFER",
            "-sDEVICE=png16m",
            "-r150",                    # 150 DPI — good quality, reasonable size
            "-dFirstPage=1",
            "-dLastPage=1",             # First page only
            f"-sOutputFile={output_path}",
            input_path,
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            if result.returncode != 0:
                stderr_msg = result.stderr.decode(errors="replace")[:400]
                logger.error(f"Ghostscript failed (exit {result.returncode}): {stderr_msg}")
                return None

            if not os.path.exists(output_path):
                logger.error("Ghostscript ran successfully but output PNG was not created.")
                return None

            with open(output_path, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            logger.error("Ghostscript timed out during vector conversion.")
            return None
        except Exception as e:
            logger.error(f"Vector conversion error: {e}")
            return None


async def convert_vector_to_png(file_data: bytes, ext: str = ".eps") -> Optional[bytes]:
    """Async wrapper for vector-to-PNG conversion."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        lambda: convert_vector_to_png_sync(file_data, ext)
    )

