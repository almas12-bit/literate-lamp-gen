import asyncio
import logging
import uuid
import os
import sys
import glob
from typing import Dict, List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import (
    GEMINI_MODELS, VIDEO_FRAME_COUNT, DEFAULT_KEYWORD_COUNT,
    MIN_KEYWORD_COUNT, MAX_KEYWORD_COUNT, AS_CATEGORIES,
    APP_DIR, BUNDLE_DIR, BIN_DIR
)
from gemini_service import key_manager, analyze_image, analyze_video_frames, sanitize_title, sanitize_keywords
from video_service import extract_frames, check_ffmpeg
from vector_service import convert_vector_to_png, check_ghostscript
from queue_manager import queue_manager, JobStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

class ApiPrefixMiddleware:
    """Rewrite /api/... to /... so frontend requests work whether prefixed or not."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/api/"):
            scope["path"] = scope["path"][4:]
        await self.app(scope, receive, send)

app = FastAPI(title="Literate Lamp", version="2.0.0")
app.add_middleware(ApiPrefixMiddleware)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

if getattr(sys, "frozen", False):
    UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
else:
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

PREVIEW_DIR = os.path.join(UPLOAD_DIR, "previews")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)
_vector_preview_locks: Dict[str, asyncio.Lock] = {}

def get_job_filepath(job_id: str) -> Optional[str]:
    matches = glob.glob(os.path.join(UPLOAD_DIR, f"{job_id}_*"))
    return matches[0] if matches else None

def get_vector_preview_path(job_id: str) -> str:
    return os.path.join(PREVIEW_DIR, f"{job_id}.png")

async def ensure_vector_preview(job_id: str, job: dict, filepath: Optional[str] = None) -> Optional[str]:
    """Return path to cached PNG preview for a vector job, converting once via Ghostscript if needed."""
    preview_path = get_vector_preview_path(job_id)
    if os.path.exists(preview_path):
        return preview_path

    lock = _vector_preview_locks.setdefault(job_id, asyncio.Lock())
    async with lock:
        if os.path.exists(preview_path):
            return preview_path
        src_path = filepath or job.get("local_file") or get_job_filepath(job_id)
        if not src_path or not os.path.exists(src_path):
            return None
        with open(src_path, "rb") as f:
            file_bytes = f.read()
        file_ext = os.path.splitext(job.get("filename") or src_path)[1].lower() or ".eps"
        png_bytes = await convert_vector_to_png(file_bytes, ext=file_ext)
        if not png_bytes:
            return None
        os.makedirs(PREVIEW_DIR, exist_ok=True)
        tmp_path = f"{preview_path}.tmp"
        with open(tmp_path, "wb") as f:
            f.write(png_bytes)
        os.replace(tmp_path, preview_path)
        return preview_path

def remove_job_file(job_id: str):
    _vector_preview_locks.pop(job_id, None)
    for target in (get_job_filepath(job_id), get_vector_preview_path(job_id)):
        if target and os.path.exists(target):
            try:
                os.remove(target)
            except Exception as e:
                logger.warning(f"Failed to remove file {target}: {e}")

def clear_upload_dir():
    _vector_preview_locks.clear()
    for folder in (UPLOAD_DIR, PREVIEW_DIR):
        if os.path.exists(folder):
            for fname in os.listdir(folder):
                fpath = os.path.join(folder, fname)
                try:
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                except Exception:
                    pass

ENV_FILE = os.path.join(APP_DIR, ".env")

def load_keys_from_env():
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            keys = []
            for line in lines:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY=") or line.startswith("GEMINI_API_KEYS="):
                    val = line.split("=", 1)[1].strip().strip('"\'')
                    for k in val.split(","):
                        if k.strip():
                            keys.append(k.strip())
            if keys:
                key_manager.set_keys(keys)
                logger.info(f"Loaded {len(keys)} API key(s) from .env")
        except Exception as e:
            logger.error(f"Error loading keys from .env: {e}")

def save_keys_to_env(keys: List[str]):
    try:
        existing_lines = []
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        new_lines = [l for l in existing_lines if not l.startswith("GEMINI_API_KEY=") and not l.startswith("GEMINI_API_KEYS=")]
        if keys:
            joined = ",".join(keys)
            new_lines.append(f'GEMINI_API_KEYS="{joined}"\n')
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        logger.error(f"Error saving keys to .env: {e}")

@app.on_event("startup")
async def startup_event():
    clear_upload_dir()
    load_keys_from_env()

selected_model: str = GEMINI_MODELS[0]
active_platforms: List[str] = ["shutterstock", "adobe_stock"]
keyword_count: int = DEFAULT_KEYWORD_COUNT
active_rules: dict = {
    "mandatory_keywords": "",
    "forbidden_words": "rendering, 3d render, octane render, blender, 4k",
    "custom_instruction": ""
}

class KeysPayload(BaseModel):
    keys_text: str

class ModelPayload(BaseModel):
    model: str

class PlatformsPayload(BaseModel):
    platforms: List[str]

class KeywordCountPayload(BaseModel):
    count: int

class RulesPayload(BaseModel):
    mandatory_keywords: Optional[str] = ""
    forbidden_words: Optional[str] = ""
    custom_instruction: Optional[str] = ""

class RetryPayload(BaseModel):
    job_ids: Optional[List[str]] = None  # None = retry all failed

async def process_job(job_id: str, job: dict) -> dict:
    file_path = job.get("local_file") or get_job_filepath(job_id)
    if not file_path or not os.path.exists(file_path):
        raise Exception("File data not found on disk")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    media_type = job.get("media_type", "image")
    mime_type = job.get("mime_type", "image/jpeg")
    model = job.get("model", selected_model)
    platforms = job.get("platforms", active_platforms)
    kw_count = job.get("keyword_count", keyword_count)
    job_rules = job.get("rules", active_rules)
    mandatory_kw = job_rules.get("mandatory_keywords", "")
    forbidden_w = job_rules.get("forbidden_words", "")
    custom_inst = job_rules.get("custom_instruction", "")

    if media_type == "video":
        frames = await extract_frames(file_bytes, frame_count=VIDEO_FRAME_COUNT)
        if not frames:
            raise Exception("Failed to extract video frames. Is ffmpeg installed?")
        ai_data = await analyze_video_frames(model, frames, platforms, kw_count, mandatory_kw, forbidden_w, custom_inst)
    elif media_type == "vector":
        preview_path = await ensure_vector_preview(job_id, job, file_path)
        if not preview_path or not os.path.exists(preview_path):
            raise Exception(
                "Failed to convert vector file to image. "
                "Please install Ghostscript from https://ghostscript.com/releases/gsdnld.html "
                "and ensure it is added to your system PATH."
            )
        with open(preview_path, "rb") as f:
            png_bytes = f.read()
        ai_data = await analyze_image(model, png_bytes, "image/png", platforms, kw_count, mandatory_kw, forbidden_w, custom_inst)
    else:
        ai_data = await analyze_image(model, file_bytes, mime_type, platforms, kw_count, mandatory_kw, forbidden_w, custom_inst)

    raw_title = ai_data.get("title", "")
    raw_magnific_title = ai_data.get("magnific_title", "")
    raw_keywords = ai_data.get("keywords", "")

    has_standard = ("shutterstock" in platforms) or ("adobe_stock" in platforms)
    has_magnific = "magnific" in platforms

    if has_magnific and not has_standard:
        magnific_title = sanitize_title(raw_magnific_title or raw_title, max_chars=100, forbidden_words=forbidden_w)
        std_title = magnific_title
    else:
        std_title = sanitize_title(raw_title or raw_magnific_title, max_chars=200, forbidden_words=forbidden_w)
        magnific_title = sanitize_title(raw_magnific_title or raw_title, max_chars=100, forbidden_words=forbidden_w) if has_magnific else ""

    result = {
        "title": std_title,
        "magnific_title": magnific_title,
        "keywords": sanitize_keywords(raw_keywords, max_count=kw_count, mandatory_keywords=mandatory_kw, forbidden_words=forbidden_w),
        "ss_category1": ai_data.get("ss_category1", ""),
        "ss_category2": ai_data.get("ss_category2", ""),
        "as_category1": str(ai_data.get("as_category1", "0")),
        "as_category2": str(ai_data.get("as_category2", "0")),
    }
    return result

queue_manager.set_processor(process_job)

@app.get("/health")
async def health():
    ffmpeg_ok = await check_ffmpeg()
    gs_ok = await check_ghostscript()
    return {
        "status": "ok",
        "ffmpeg": ffmpeg_ok,
        "ghostscript": gs_ok,
        "keys_loaded": len(key_manager.keys),
        "model": selected_model,
        "platforms": active_platforms,
        "keyword_count": keyword_count,
        "rules": active_rules
    }

@app.get("/rules")
async def get_rules():
    return active_rules

@app.post("/rules")
async def update_rules(payload: RulesPayload):
    global active_rules
    active_rules["mandatory_keywords"] = payload.mandatory_keywords or ""
    active_rules["forbidden_words"] = payload.forbidden_words or ""
    active_rules["custom_instruction"] = payload.custom_instruction or ""
    return active_rules

@app.get("/models")
async def get_models():
    return {"models": GEMINI_MODELS}

@app.get("/categories")
async def get_categories():
    from config import SS_CATEGORIES
    return {"shutterstock": SS_CATEGORIES, "adobe_stock": AS_CATEGORIES}

@app.post("/keys")
async def set_keys(payload: KeysPayload):
    lines = [l.strip() for l in payload.keys_text.splitlines() if l.strip()]
    if not lines:
        raise HTTPException(400, "No valid API keys provided")
    key_manager.set_keys(lines)
    save_keys_to_env(lines)
    return {"message": f"{len(lines)} key(s) loaded and saved", "count": len(lines)}

@app.get("/keys/status")
async def keys_status():
    return {"keys": key_manager.get_keys_info()}

@app.post("/keys/test")
async def test_keys():
    if not key_manager.keys:
        return {"ok": False, "message": "Belum ada API key yang terdaftar. Masukkan API key terlebih dahulu."}
    try:
        # Use gemini-3.5-flash-lite (verified active & fast) to test key validity
        test_model = "gemini-3.5-flash-lite" if "gemini-3.5-flash-lite" in GEMINI_MODELS else selected_model
        res = await call_gemini(
            model=test_model,
            parts=[{"text": "Test connection. Return JSON: {\"status\": \"ok\"}"}],
            max_retries=len(key_manager.keys)
        )
        return {
            "ok": True,
            "message": f"Koneksi Berhasil! API Key aktif dan terhubung ke Google AI Studio ({test_model}).",
            "keys": key_manager.get_keys_info()
        }
    except Exception as e:
        logger.error(f"Test keys error: {e}")
        return {
            "ok": False,
            "message": f"Koneksi Gagal: {str(e)}",
            "keys": key_manager.get_keys_info()
        }

@app.post("/model")
async def set_model(payload: ModelPayload):
    global selected_model
    if payload.model not in GEMINI_MODELS:
        raise HTTPException(400, f"Unknown model: {payload.model}")
    selected_model = payload.model
    return {"model": selected_model}

@app.post("/platforms")
async def set_platforms(payload: PlatformsPayload):
    global active_platforms
    active_platforms = payload.platforms
    return {"platforms": active_platforms}

@app.post("/keyword-count")
async def set_keyword_count(payload: KeywordCountPayload):
    global keyword_count
    if not (MIN_KEYWORD_COUNT <= payload.count <= MAX_KEYWORD_COUNT):
        raise HTTPException(400, f"Count must be between {MIN_KEYWORD_COUNT} and {MAX_KEYWORD_COUNT}")
    keyword_count = payload.count
    return {"count": keyword_count}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    if not key_manager.keys:
        raise HTTPException(400, "No API keys loaded. Please add keys first.")
    job_ids = []
    for file in files:
        job_id = str(uuid.uuid4())
        safe_name = "".join(c for c in (file.filename or "media") if c.isalnum() or c in "._- ")
        dest_path = os.path.join(UPLOAD_DIR, f"{job_id}_{safe_name}")
        file_bytes = await file.read()
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        fname_lower = (file.filename or "").lower()
        ct = (file.content_type or "").lower()
        if ct.startswith("video/") or any(fname_lower.endswith(e) for e in (".mp4", ".mov", ".avi", ".mkv", ".webm")):
            media_type = "video"
        elif fname_lower.endswith(".ai") or fname_lower.endswith(".eps") or \
                ct in ("application/postscript", "image/x-eps", "application/illustrator",
                        "application/eps", "image/eps"):
            media_type = "vector"
        else:
            media_type = "image"
        queue_manager.add_job(job_id, {
            "filename": file.filename,
            "mime_type": file.content_type,
            "media_type": media_type,
            "local_file": dest_path,
            "model": selected_model,
            "platforms": list(active_platforms),
            "keyword_count": keyword_count,
            "rules": dict(active_rules),
            "title": "", "magnific_title": "", "keywords": "",
            "ss_category1": "", "ss_category2": "",
            "as_category1": "0", "as_category2": "0",
            "editorial": "no", "mature_content": "no",
            "illustration": "no", "is_ai": "no", "releases": "",
        })
        job_ids.append(job_id)
    return {"job_ids": job_ids, "count": len(job_ids)}

@app.get("/media/{job_id}")
async def get_media(job_id: str):
    filepath = get_job_filepath(job_id)
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(404, "Media file not found")
    job = queue_manager.jobs.get(job_id, {})
    if job.get("media_type") == "vector" or filepath.lower().endswith((".ai", ".eps")):
        preview_path = await ensure_vector_preview(job_id, job, filepath)
        if not preview_path or not os.path.exists(preview_path):
            raise HTTPException(422, "Vector preview unavailable")
        return FileResponse(preview_path, media_type="image/png")
    mime_type = job.get("mime_type")
    return FileResponse(filepath, media_type=mime_type, filename=job.get("filename"))

@app.get("/queue/status")
async def queue_status():
    return queue_manager.get_status()

@app.get("/queue/jobs")
async def queue_jobs():
    jobs_out = []
    for job_id in queue_manager.queue:
        job = queue_manager.jobs.get(job_id, {})
        jobs_out.append({
            "id": job_id,
            "filename": job.get("filename",""),
            "media_type": job.get("media_type","image"),
            "status": job.get("status","pending"),
            "media_url": f"/media/{job_id}" if get_job_filepath(job_id) else "",
            "title": job.get("title",""),
            "magnific_title": job.get("magnific_title",""),
            "keywords": job.get("keywords",""),
            "ss_category1": job.get("ss_category1",""),
            "ss_category2": job.get("ss_category2",""),
            "as_category1": job.get("as_category1","0"),
            "as_category2": job.get("as_category2","0"),
            "editorial": job.get("editorial","no"),
            "mature_content": job.get("mature_content","no"),
            "illustration": job.get("illustration","no"),
            "is_ai": job.get("is_ai","no"),
            "releases": job.get("releases",""),
            "error": job.get("error",""),
            "platforms": job.get("platforms", ["shutterstock"]),
        })
    return {"jobs": jobs_out}

@app.post("/queue/start")
async def queue_start():
    await queue_manager.start()
    return {"state": queue_manager.state}

@app.post("/queue/pause")
async def queue_pause():
    await queue_manager.pause()
    return {"state": queue_manager.state}

@app.post("/queue/stop")
async def queue_stop():
    await queue_manager.stop()
    return {"state": queue_manager.state}

@app.post("/queue/reset")
async def queue_reset():
    clear_upload_dir()
    await queue_manager.reset()
    return {"state": queue_manager.state}

@app.post("/queue/retry")
async def queue_retry(payload: RetryPayload):
    """Retry failed/error/cancelled jobs. Preserves done jobs."""
    target_ids = payload.job_ids
    if target_ids is None:
        target_ids = [jid for jid, j in queue_manager.jobs.items() if j.get("status") in ("error","cancelled")]
    
    retried = 0
    for job_id in target_ids:
        if job_id in queue_manager.jobs:
            job = queue_manager.jobs[job_id]
            if job.get("status") in ("error", "cancelled"):
                if job_id not in queue_manager.queue:
                    queue_manager.queue.append(job_id)
                queue_manager.jobs[job_id]["status"] = "pending"
                queue_manager.jobs[job_id]["error"] = ""
                retried += 1
    return {"retried": retried}

@app.patch("/queue/jobs/{job_id}")
async def update_job(job_id: str, data: dict):
    if job_id not in queue_manager.jobs:
        raise HTTPException(404, "Job not found")
    allowed = {"title","magnific_title","keywords","ss_category1","ss_category2","as_category1","as_category2","editorial","mature_content","illustration","is_ai","releases"}
    queue_manager.update_job(job_id, **{k:v for k,v in data.items() if k in allowed})
    return {"ok": True}

@app.delete("/queue/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id not in queue_manager.jobs:
        raise HTTPException(404, "Job not found")
    queue_manager.jobs.pop(job_id, None)
    remove_job_file(job_id)
    if job_id in queue_manager.queue:
        queue_manager.queue.remove(job_id)
    return {"ok": True}

@app.delete("/queue/jobs")
async def delete_jobs(ids: List[str]):
    for job_id in ids:
        queue_manager.jobs.pop(job_id, None)
        remove_job_file(job_id)
        if job_id in queue_manager.queue:
            queue_manager.queue.remove(job_id)
    return {"ok": True, "deleted": len(ids)}

# -------------------------------------------------------------
# Frontend Static Files Serving & SPA Fallback
# -------------------------------------------------------------
if getattr(sys, "frozen", False):
    FRONTEND_DIST = os.path.join(BUNDLE_DIR, "dist")
else:
    FRONTEND_DIST = os.path.join(APP_DIR, "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend build not found. Run npm run build."}

    @app.get("/{full_path:path}")
    async def serve_frontend_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("media/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="File not found")

