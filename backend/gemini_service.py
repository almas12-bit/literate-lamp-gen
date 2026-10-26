import httpx
import asyncio
import base64
import json
import logging
import time
from typing import List, Optional, Dict
from config import GEMINI_API_BASE, SS_CATEGORIES, AS_CATEGORIES

logger = logging.getLogger(__name__)

class KeyStatus:
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"

class ApiKeyManager:
    def __init__(self):
        self.keys: List[str] = []
        self.statuses: Dict[str, str] = {}
        self.error_messages: Dict[str, str] = {}
        self.current_index: int = 0
        self._lock = asyncio.Lock()
        self._rate_limit_reset: Dict[str, float] = {}

    def set_keys(self, keys: List[str]):
        self.keys = [k.strip() for k in keys if k.strip()]
        self.statuses = {k: KeyStatus.ACTIVE for k in self.keys}
        self.error_messages = {}
        self.current_index = 0
        self._rate_limit_reset = {}

    def get_keys_info(self) -> List[Dict]:
        return [
            {
                "key": f"{k[:4]}...{k[-4:]}" if len(k) > 10 else f"...{k[-4:]}",
                "status": self.statuses.get(k, KeyStatus.ACTIVE),
                "error": self.error_messages.get(k, "")
            }
            for k in self.keys
        ]

    async def get_next_key(self) -> Optional[str]:
        async with self._lock:
            now = time.time()
            for k, reset_time in list(self._rate_limit_reset.items()):
                if now > reset_time:
                    self.statuses[k] = KeyStatus.ACTIVE
                    del self._rate_limit_reset[k]
            for _ in range(len(self.keys)):
                key = self.keys[self.current_index % len(self.keys)]
                self.current_index = (self.current_index + 1) % len(self.keys)
                if self.statuses.get(key) == KeyStatus.ACTIVE:
                    return key
            return None

    async def mark_rate_limited(self, key: str):
        async with self._lock:
            self.statuses[key] = KeyStatus.RATE_LIMITED
            self._rate_limit_reset[key] = time.time() + 65

    async def mark_error(self, key: str, message: str = ""):
        async with self._lock:
            self.statuses[key] = KeyStatus.ERROR
            if message:
                self.error_messages[key] = message

key_manager = ApiKeyManager()

async def call_gemini(model: str, parts: List[Dict], max_retries: int = None) -> Dict:
    max_retries = max_retries or max(len(key_manager.keys) * 2, 3)
    last_err_msg = ""
    for attempt in range(max_retries):
        key = await key_manager.get_next_key()
        if not key:
            raise Exception(f"All API keys exhausted or rate-limited. {last_err_msg}".strip())
        
        # Dual-support: send via official SDK header (x-goog-api-key), with automatic query param fallback
        url = f"{GEMINI_API_BASE}/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        }
        gen_config = {
            "responseMimeType": "application/json",
            "temperature": 0.3
        }
        payload = {"contents": [{"parts": parts}], "generationConfig": gen_config}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # 1. Primary: Official Google GenAI SDK header (supports both AIza and AQ keys)
                response = await client.post(url, headers=headers, json=payload)

                # 2. Fallback: If header rejected with 401/403, retry via URL query parameter ?key=...
                if response.status_code in (401, 403):
                    fallback_resp = await client.post(f"{url}?key={key}", json=payload)
                    if fallback_resp.status_code == 200:
                        response = fallback_resp
            
            if response.status_code == 200:
                result = response.json()
                raw = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw)
            
            err_text = response.text
            logger.error(f"Gemini API returned status {response.status_code}: {err_text}")
            
            try:
                err_data = response.json()
                msg = err_data.get("error", {}).get("message", err_text[:120])
            except Exception:
                msg = err_text[:120]
            
            last_err_msg = f"Last error ({response.status_code}): {msg}"

            if response.status_code == 429:
                await key_manager.mark_rate_limited(key)
                await asyncio.sleep(1)
                continue
            
            if response.status_code in (503, 404):
                # 503 (High Demand) or 404 (Model Retired): Auto-route to verified working models
                logger.warning(f"Google status {response.status_code} for '{model}'. Routing to verified fallback models...")
                alt_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]
                for alt_m in alt_models:
                    if alt_m != model:
                        alt_url = f"{GEMINI_API_BASE}/{alt_m}:generateContent"
                        try:
                            async with httpx.AsyncClient(timeout=120.0) as client:
                                alt_resp = await client.post(alt_url, headers=headers, json=payload)
                            if alt_resp.status_code == 200:
                                result = alt_resp.json()
                                raw = result["candidates"][0]["content"]["parts"][0]["text"]
                                logger.info(f"Job completed successfully using verified fallback model '{alt_m}'!")
                                return json.loads(raw)
                        except Exception:
                            pass
                if response.status_code == 404:
                    raise Exception(f"Model '{model}' tidak tersedia di akun Anda: {msg}")
                logger.warning("Google servers currently busy. Waiting 3s before retry...")
                await asyncio.sleep(3)
                continue

            if response.status_code in (400, 401, 403):
                await key_manager.mark_error(key, f"HTTP {response.status_code}: {msg}")
                if len(key_manager.keys) <= 1:
                    raise Exception(f"Gemini API error ({response.status_code}): {msg}")
            
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if "Gemini API error" in str(e):
                raise
            logger.error(f"Request error: {e}")
            last_err_msg = str(e)
            await asyncio.sleep(2)
    raise Exception(f"Failed after {max_retries} attempts. {last_err_msg}".strip())

import re

def sanitize_title(title: str, max_chars: int = 200, forbidden_words: str = "") -> str:
    if not title:
        return ""
    t = str(title).strip().strip('"\'')
    if t.lower().startswith("title:"):
        t = t[6:].strip().strip('"\'')

    # Remove any forbidden words/phrases (case-insensitive)
    if forbidden_words:
        fw_list = [w.strip() for w in forbidden_words.split(",") if w.strip()]
        for fw in fw_list:
            pattern = re.compile(r'\b' + re.escape(fw) + r'\b', re.IGNORECASE)
            t = pattern.sub("", t)

    t = " ".join(t.split())
    if len(t) <= max_chars:
        return t
    truncated = t[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > 50:
        truncated = truncated[:last_space]
    return truncated.rstrip(",;:- ")

def sanitize_keywords(keywords_raw: str, max_count: int = 49, mandatory_keywords: str = "", forbidden_words: str = "") -> str:
    if not keywords_raw and not mandatory_keywords:
        return ""
    target_max = min(max_count, 49)

    # Parse forbidden words into a normalized set
    forbidden_set = set()
    if forbidden_words:
        for fw in forbidden_words.split(","):
            cleaned_fw = fw.strip().lower()
            if cleaned_fw:
                forbidden_set.add(cleaned_fw)

    # Parse mandatory keywords (preserving order, skipping forbidden)
    mandatory_list = []
    if mandatory_keywords:
        for mw in mandatory_keywords.split(","):
            cleaned_mw = mw.strip().lower()
            if cleaned_mw and cleaned_mw not in forbidden_set and cleaned_mw not in mandatory_list:
                mandatory_list.append(cleaned_mw)

    raw_list = [k.strip().lower() for k in str(keywords_raw or "").replace("\n", ",").split(",") if k.strip()]

    # Mandatory keywords come first
    seen = set()
    cleaned = []

    for kw in mandatory_list:
        seen.add(kw)
        cleaned.append(kw)
        if len(cleaned) >= target_max:
            return ", ".join(cleaned)

    for kw in raw_list:
        kw_clean = kw.strip('"\'.- ')
        if not kw_clean or kw_clean in forbidden_set:
            continue
        if kw_clean not in seen:
            seen.add(kw_clean)
            cleaned.append(kw_clean)
            if len(cleaned) >= target_max:
                break

    return ", ".join(cleaned)

def build_prompt(media_label: str, platforms: List[str], keyword_count: int, mandatory_keywords: str = "", forbidden_words: str = "", custom_instruction: str = "") -> str:
    target_kw = min(max(keyword_count, 15), 49)
    ss_cats = ", ".join(SS_CATEGORIES)
    as_cats = ", ".join([f"{k}={v}" for k, v in AS_CATEGORIES.items()])

    fields = {
        "title": "descriptive English title, strictly 100-180 characters, NEVER exceed 200 characters",
        "keywords": f"exactly {target_kw} comma-separated English keywords ordered by relevance"
    }

    if "shutterstock" in platforms:
        fields["ss_category1"] = f"one from: {ss_cats}"
        fields["ss_category2"] = f"another from same list or empty string"

    if "adobe_stock" in platforms:
        fields["as_category1"] = f"numeric code only, from: {as_cats}"
        fields["as_category2"] = f"another numeric code or 0 for none"

    fields_str = json.dumps(fields, indent=2)

    rules = [
        "1. TITLE LENGTH: The title MUST BE strictly UNDER 200 characters (aim for 120-170 characters). NEVER exceed 200 characters under any circumstance.",
        "2. TITLE CONTENT: Plain descriptive English sentence stating what is visible. DO NOT include camera gear/settings, and DO NOT include generic buzzwords like '4K', 'HD', 'masterpiece', 'trending', or 'wallpaper'.",
        f"3. KEYWORDS COUNT: Output EXACTLY {target_kw} keywords. NEVER exceed {target_kw} keywords and NEVER exceed 49 keywords.",
        "4. KEYWORDS RELEVANCE: Lowercase, comma-separated, ordered by relevance (most important first). NO duplicates.",
        "5. TRADEMARKS: Absolutely NO trademarked brand names (e.g. Apple, Nike, Sony) unless editorial."
    ]

    rule_num = 6
    if mandatory_keywords and mandatory_keywords.strip():
        rules.append(f"{rule_num}. MANDATORY KEYWORDS: You MUST include these keywords in the output list: {mandatory_keywords.strip()}.")
        rule_num += 1

    if forbidden_words and forbidden_words.strip():
        rules.append(f"{rule_num}. FORBIDDEN WORDS: NEVER use any of these words in title or keywords: {forbidden_words.strip()}.")
        rule_num += 1

    if custom_instruction and custom_instruction.strip():
        rules.append(f"{rule_num}. CUSTOM INSTRUCTIONS: {custom_instruction.strip()}.")
        rule_num += 1

    rules_str = "\n".join(rules)

    return (
        f"Analyze this {media_label} and generate commercial stock photo/video metadata.\n"
        f"Return ONLY a valid JSON object matching this structure:\n{fields_str}\n\n"
        f"CRITICAL RULES & STRICT PROHIBITIONS:\n{rules_str}"
    )

async def analyze_image(model: str, image_data: bytes, mime_type: str, platforms: List[str], keyword_count: int, mandatory_keywords: str = "", forbidden_words: str = "", custom_instruction: str = "") -> Dict:
    b64 = base64.b64encode(image_data).decode()
    parts = [
        {"text": build_prompt("image", platforms, keyword_count, mandatory_keywords, forbidden_words, custom_instruction)},
        {"inlineData": {"mimeType": mime_type, "data": b64}}
    ]
    return await call_gemini(model, parts)

async def analyze_video_frames(model: str, frames: List[bytes], platforms: List[str], keyword_count: int, mandatory_keywords: str = "", forbidden_words: str = "", custom_instruction: str = "") -> Dict:
    parts = [{"text": build_prompt("video (frames shown)", platforms, keyword_count, mandatory_keywords, forbidden_words, custom_instruction)}]
    for frame in frames:
        b64 = base64.b64encode(frame).decode()
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": b64}})
    return await call_gemini(model, parts)
