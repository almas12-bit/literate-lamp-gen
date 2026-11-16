import asyncio
import subprocess
import tempfile
import os
import shutil
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from config import BIN_DIR

logger = logging.getLogger(__name__)

# Use thread pool for subprocess calls (Windows Python 3.14 compatibility)
_executor = ThreadPoolExecutor(max_workers=4)


def find_ffmpeg() -> str:
    """Find ffmpeg binary: first in BIN_DIR, then in PATH."""
    if os.path.isdir(BIN_DIR):
        candidate = os.path.join(BIN_DIR, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.isfile(candidate):
            return candidate
    return shutil.which("ffmpeg") or "ffmpeg"


def find_ffprobe() -> str:
    """Find ffprobe binary: first in BIN_DIR, then in PATH."""
    if os.path.isdir(BIN_DIR):
        candidate = os.path.join(BIN_DIR, "ffprobe.exe" if os.name == "nt" else "ffprobe")
        if os.path.isfile(candidate):
            return candidate
    return shutil.which("ffprobe") or "ffprobe"


def _run_cmd(cmd: list, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a subprocess command synchronously."""
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout
    )


async def _run_cmd_async(cmd: list, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run subprocess in thread pool to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: _run_cmd(cmd, timeout))


def check_ffmpeg_sync() -> bool:
    """Check if ffmpeg is available."""
    ffmpeg_bin = find_ffmpeg()
    try:
        result = subprocess.run(
            [ffmpeg_bin, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


async def check_ffmpeg() -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, check_ffmpeg_sync)


def get_video_duration_sync(input_path: str) -> Optional[float]:
    """Get video duration using ffprobe synchronously."""
    ffprobe_bin = find_ffprobe()
    try:
        result = subprocess.run(
            [
                ffprobe_bin, "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                input_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )
        duration_str = result.stdout.decode().strip()
        if duration_str:
            return float(duration_str)
    except Exception as e:
        logger.error(f"ffprobe error: {e}")
    return None


def extract_frames_sync(video_data: bytes, frame_count: int = 3) -> List[bytes]:
    """Extract frames synchronously using ffmpeg."""
    ffmpeg_bin = find_ffmpeg()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input_video")

        with open(input_path, "wb") as f:
            f.write(video_data)

        duration = get_video_duration_sync(input_path)
        if duration is None or duration <= 0:
            logger.error("Could not determine video duration")
            return []

        interval = duration / (frame_count + 1)
        timestamps = [interval * (i + 1) for i in range(frame_count)]

        frames = []
        for i, ts in enumerate(timestamps):
            frame_path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
            cmd = [
                ffmpeg_bin, "-y",
                "-ss", str(ts),
                "-i", input_path,
                "-frames:v", "1",
                "-q:v", "3",
                "-vf", "scale=1280:-1",
                frame_path
            ]
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                if os.path.exists(frame_path):
                    with open(frame_path, "rb") as f:
                        frames.append(f.read())
                    logger.debug(f"Extracted frame at {ts:.2f}s")
                else:
                    logger.warning(f"Frame not created at {ts:.2f}s, stderr: {result.stderr.decode()[:200]}")
            except subprocess.TimeoutExpired:
                logger.error(f"ffmpeg timed out at frame {i}")
            except Exception as e:
                logger.error(f"Frame extraction error: {e}")

        logger.info(f"Extracted {len(frames)}/{frame_count} frames")
        return frames


async def extract_frames(video_data: bytes, frame_count: int = 3) -> List[bytes]:
    """Async wrapper for frame extraction."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: extract_frames_sync(video_data, frame_count))
