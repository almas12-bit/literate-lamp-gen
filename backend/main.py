import asyncio
import logging
import uuid
import os
import glob
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import GEMINI_MODELS, VIDEO_FRAME_COUNT, DEFAULT_KEYWORD_COUNT, MIN_KEYWORD_COUNT, MAX_KEYWORD_COUNT, AS_CATEGORIES
from gemini_service import key_manager, analyze_image, analyze_video_frames, sanitize_title, sanitize_keywords
from video_service import extract_frames, check_ffmpeg
from queue_manager import queue_manager, JobStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Shutterstock AI", version="2.0.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_job_filepath(job_id: str) -> Optional[str]:
    matches = glob.glob(os.path.join(UPLOAD_DIR, f"{job_id}_*"))
    return matches[0] if matches else None

def remove_job_file(job_id: str):
    filepath = get_job_filepath(job_id)
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            logger.warning(f"Failed to remove file {filepath}: {e}")

def clear_upload_dir():
    if os.path.exists(UPLOAD_DIR):
        for fname in os.listdir(UPLOAD_DIR):
            fpath = os.path.join(UPLOAD_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception:
                pass

@app.on_event("startup")
async def startup_event():
    clear_upload_dir()

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
    else:
        ai_data = await analyze_image(model, file_bytes, mime_type, platforms, kw_count, mandatory_kw, forbidden_w, custom_inst)

    raw_title = ai_data.get("title", "")
    raw_keywords = ai_data.get("keywords", "")

    result = {
        "title": sanitize_title(raw_title, max_chars=200, forbidden_words=forbidden_w),
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
    return {
        "status": "ok",
        "ffmpeg": ffmpeg_ok,
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
    return {"message": f"{len(lines)} key(s) loaded", "count": len(lines)}

@app.get("/keys/status")
async def keys_status():
    return {"keys": key_manager.get_keys_info()}

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
        media_type = "video" if (file.content_type or "").startswith("video/") else "image"
        queue_manager.add_job(job_id, {
            "filename": file.filename,
            "mime_type": file.content_type,
            "media_type": media_type,
            "local_file": dest_path,
            "model": selected_model,
            "platforms": list(active_platforms),
            "keyword_count": keyword_count,
            "rules": dict(active_rules),
            "title": "", "keywords": "",
            "ss_category1": "", "ss_category2": "",
            "as_category1": "0", "as_category2": "0",
            "editorial": "no", "mature_content": "no",
            "illustration": "no", "releases": "",
        })
        job_ids.append(job_id)
    return {"job_ids": job_ids, "count": len(job_ids)}

@app.get("/media/{job_id}")
async def get_media(job_id: str):
    filepath = get_job_filepath(job_id)
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(404, "Media file not found")
    job = queue_manager.jobs.get(job_id, {})
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
            "keywords": job.get("keywords",""),
            "ss_category1": job.get("ss_category1",""),
            "ss_category2": job.get("ss_category2",""),
            "as_category1": job.get("as_category1","0"),
            "as_category2": job.get("as_category2","0"),
            "editorial": job.get("editorial","no"),
            "mature_content": job.get("mature_content","no"),
            "illustration": job.get("illustration","no"),
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
    allowed = {"title","keywords","ss_category1","ss_category2","as_category1","as_category2","editorial","mature_content","illustration","releases"}
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
