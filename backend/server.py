from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import asyncio
import base64
import logging
import random
import io
import bcrypt
import jwt
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta

from PIL import Image, ImageDraw, ImageFont
from emergentintegrations.llm.chat import LlmChat, UserMessage

from demo_news import DEMO_NEWS, CATEGORIES, SEED_ARTICLES

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Auth config
JWT_SECRET = os.environ.get('JWT_SECRET', 'change-me')
JWT_ALGORITHM = "HS256"
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@ghaziabadtimes.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Gzb#Times@2026$Secure')
SITE_NAME = os.environ.get('SITE_NAME', 'Ghaziabad Times')

# News provider config
NEWS_PROVIDER = os.environ.get('NEWS_PROVIDER', 'gnews').lower()
GNEWS_API_KEY = os.environ.get('GNEWS_API_KEY', '').strip()
NEWSDATA_API_KEY = os.environ.get('NEWSDATA_API_KEY', '').strip()

# Auto-fetch config
AUTO_FETCH_ENABLED = os.environ.get('AUTO_FETCH_ENABLED', 'true').lower() == 'true'
AUTO_FETCH_INTERVAL_HOURS = float(os.environ.get('AUTO_FETCH_INTERVAL_HOURS', '1'))
AUTO_FETCH_COUNT = int(os.environ.get('AUTO_FETCH_COUNT', '10'))

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ----------------------------- Models -----------------------------
class Fact(BaseModel):
    type: str
    value: str


class Article(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_title: str
    source_content: str = ""
    source_name: str = ""
    category: str = "दुनिया"
    rewritten_headline: str = ""
    rewritten_article: str = ""
    facts: List[Fact] = Field(default_factory=list)
    image_prompt: str = ""
    image_url: str = ""          # data URL (base64) or external URL
    watermark_text: str = "Ghaziabad Times"
    status: str = "pending"      # pending | published | rejected
    ai_processed: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_at: Optional[str] = None


class EditArticle(BaseModel):
    rewritten_headline: Optional[str] = None
    rewritten_article: Optional[str] = None


class FetchRequest(BaseModel):
    count: int = 3
    category: Optional[str] = None


class ManualUpload(BaseModel):
    title: Optional[str] = ""
    content: Optional[str] = ""
    url: Optional[str] = ""
    category: str = "दुनिया"


class Settings(BaseModel):
    watermark_text: str = "Ghaziabad Times"


# ----------------------------- AI helpers -----------------------------
REWRITE_SYSTEM = (
    "आप एक अनुभवी हिंदी समाचार संपादक और अनुवादक हैं। आपको अंग्रेज़ी की एक विदेशी खबर दी जाएगी। "
    "आपका काम:\n"
    "1. एक अत्यधिक आकर्षक और क्लिकेबल हिंदी हेडलाइन बनाना (clickbait जैसा पर सच्चाई से समझौता किए बिना)।\n"
    "2. पूरे लेख को शुद्ध, व्याकरण-सम्मत, प्रवाहमयी हिंदी में अपने शब्दों में दोबारा लिखना।\n"
    "सबसे महत्वपूर्ण नियम — तथ्य सुरक्षा (FACT PROTECTION):\n"
    "- सभी संख्यात्मक आँकड़े (numbers, percentages, money, scores), तारीख़ें, और समय बिल्कुल वैसे ही रखें जैसे मूल में हैं — अंकों में कोई बदलाव नहीं।\n"
    "- व्यक्तियों के नाम, संगठनों और स्थानों के नाम न बदलें; उन्हें सही ढंग से लिखें और पहली बार आने पर कोष्ठक में मूल अंग्रेज़ी नाम भी दें, जैसे: क्रिस्टीन लगार्ड (Christine Lagarde)।\n"
    "- कोई भी नई जानकारी न जोड़ें और कोई तथ्य न हटाएं।\n"
    "साथ ही मूल खबर से निकाले गए मुख्य तथ्यों की एक सूची दें (नाम, स्थान, आँकड़े, तारीख़)।\n"
    "एक छोटा अंग्रेज़ी image_prompt भी दें जो इस खबर के लिए एक प्रासंगिक फ़ोटो-यथार्थवादी समाचार तस्वीर का वर्णन करे (कोई टेक्स्ट नहीं)।\n"
    "केवल इस JSON प्रारूप में उत्तर दें, बिना किसी अतिरिक्त टेक्स्ट के:\n"
    '{"rewritten_headline": "...", "rewritten_article": "...", '
    '"facts": [{"type": "नाम|स्थान|आँकड़ा|तारीख़", "value": "..."}], "image_prompt": "..."}'
)


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


async def ai_rewrite(item: dict) -> dict:
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"rewrite-{uuid.uuid4()}",
        system_message=REWRITE_SYSTEM,
    ).with_model("openai", "gpt-5.4")
    prompt = (
        f"शीर्षक (Title): {item['source_title']}\n\n"
        f"लेख (Article): {item['source_content']}\n\n"
        f"स्रोत (Source): {item.get('source_name', '')}"
    )
    resp = await chat.send_message(UserMessage(text=prompt))
    data = _extract_json(resp)
    return data


async def ai_generate_image(prompt: str) -> Optional[bytes]:
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"img-{uuid.uuid4()}",
            system_message="You are a professional news photo generator.",
        ).with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
        full_prompt = (
            f"A high quality, photo-realistic editorial news photograph: {prompt}. "
            "Cinematic lighting, journalistic style, no text or letters in the image."
        )
        _text, images = await chat.send_message_multimodal_response(UserMessage(text=full_prompt))
        if images:
            return base64.b64decode(images[0]['data'])
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
    return None


def _load_font(size: int):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def add_watermark(image_bytes: bytes, text: str = "MyNews") -> str:
    """Bake a semi-transparent watermark and return a JPEG data URL."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    max_w = 1280
    if img.width > max_w:
        img = img.resize((max_w, int(img.height * max_w / img.width)))
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_size = max(22, img.width // 22)
    font = _load_font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = int(font_size * 0.4)
    x, y = img.width - tw - pad * 2, img.height - th - pad * 2
    draw.rectangle([x - pad, y - pad, x + tw + pad, y + th + pad + pad // 2],
                   fill=(200, 16, 46, 180))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 235))
    watermarked = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    buf = io.BytesIO()
    watermarked.save(buf, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


async def process_item(item: dict, watermark_text: str) -> Article:
    art = Article(
        source_title=item["source_title"],
        source_content=item.get("source_content", ""),
        source_name=item.get("source_name", ""),
        category=item.get("category", "दुनिया"),
        watermark_text=watermark_text,
    )
    try:
        rewrite_task = ai_rewrite(item)
        rewrite = await rewrite_task
        art.rewritten_headline = rewrite.get("rewritten_headline", item["source_title"])
        art.rewritten_article = rewrite.get("rewritten_article", item.get("source_content", ""))
        art.facts = [Fact(**f) for f in rewrite.get("facts", []) if isinstance(f, dict) and f.get("value")]
        art.image_prompt = rewrite.get("image_prompt", art.rewritten_headline)
        img_bytes = await ai_generate_image(art.image_prompt)
        if img_bytes:
            art.image_url = add_watermark(img_bytes, watermark_text)
        art.ai_processed = True
    except Exception as e:
        logger.error(f"AI processing failed for '{item['source_title']}': {e}")
        art.rewritten_headline = item["source_title"]
        art.rewritten_article = item.get("source_content", "")
    return art


import re
import requests as _requests


def fetch_url_text(url: str) -> tuple:
    """Best-effort fetch of an article URL; returns (title, text)."""
    try:
        resp = _requests.get(url, timeout=12, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MyNewsBot/1.0)"
        })
        html = resp.text
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
        # keep paragraph text
        body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
        paras = re.findall(r"<p[^>]*>(.*?)</p>", body, re.I | re.S)
        text = " ".join(re.sub(r"<[^>]+>", "", p) for p in paras)
        text = re.sub(r"\s+", " ", text).strip()
        return title, text[:4000]
    except Exception as e:
        logger.error(f"URL fetch failed: {e}")
        return "", ""


async def get_watermark_text() -> str:
    doc = await db.settings.find_one({"_id": "global"})
    return doc.get("watermark_text", SITE_NAME) if doc else SITE_NAME


# ----------------------------- Auth (security hardening) -----------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(email: str) -> str:
    payload = {
        "sub": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="प्रमाणीकरण आवश्यक है")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="अमान्य टोकन")
        user = await db.users.find_one({"email": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="उपयोगकर्ता नहीं मिला")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="सत्र समाप्त हो गया, दोबारा लॉगिन करें")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="अमान्य टोकन")


# ----------------------------- Real News Provider -----------------------------
GNEWS_CATEGORY = {
    "दुनिया": "world", "व्यापार": "business", "तकनीक": "technology",
    "खेल": "sports", "मनोरंजन": "entertainment", "राजनीति": "nation",
}


def _gnews_fetch(category: Optional[str], count: int) -> list:
    cat = GNEWS_CATEGORY.get(category or "", "world")
    params = {"category": cat, "lang": "en", "max": max(1, min(count, 10)), "apikey": GNEWS_API_KEY}
    resp = _requests.get("https://gnews.io/api/v4/top-headlines", params=params, timeout=15)
    resp.raise_for_status()
    out = []
    hindi_cat = category or "दुनिया"
    for a in resp.json().get("articles", []):
        content = (a.get("content") or "") + " " + (a.get("description") or "")
        out.append({
            "source_title": a.get("title", "").strip(),
            "source_content": content.strip(),
            "source_name": (a.get("source") or {}).get("name", "GNews"),
            "category": hindi_cat,
        })
    return [x for x in out if x["source_title"]]


def _newsdata_fetch(category: Optional[str], count: int) -> list:
    cat = GNEWS_CATEGORY.get(category or "", "world")
    params = {"apikey": NEWSDATA_API_KEY, "language": "en", "category": cat}
    resp = _requests.get("https://newsdata.io/api/1/latest", params=params, timeout=15)
    resp.raise_for_status()
    out = []
    hindi_cat = category or "दुनिया"
    for a in resp.json().get("results", [])[:max(1, min(count, 10))]:
        content = (a.get("content") or "") + " " + (a.get("description") or "")
        out.append({
            "source_title": (a.get("title") or "").strip(),
            "source_content": content.strip(),
            "source_name": a.get("source_name", "NewsData"),
            "category": hindi_cat,
        })
    return [x for x in out if x["source_title"]]


async def fetch_source_items(category: Optional[str], count: int) -> tuple:
    """Return (items, source_label). Uses real News API when a key exists, else demo pool."""
    if NEWS_PROVIDER == "gnews" and GNEWS_API_KEY:
        try:
            items = await asyncio.to_thread(_gnews_fetch, category, count)
            if items:
                return items, "gnews"
        except Exception as e:
            logger.error(f"GNews fetch failed, falling back to demo: {e}")
    elif NEWS_PROVIDER == "newsdata" and NEWSDATA_API_KEY:
        try:
            items = await asyncio.to_thread(_newsdata_fetch, category, count)
            if items:
                return items, "newsdata"
        except Exception as e:
            logger.error(f"NewsData fetch failed, falling back to demo: {e}")

    # demo fallback
    pool = DEMO_NEWS[:]
    if category:
        cat_pool = [n for n in pool if n["category"] == category]
        pool = cat_pool or pool
    random.shuffle(pool)
    return pool, "demo"


async def run_fetch_pipeline(count: int, category: Optional[str], allow_duplicates: bool = True) -> List["Article"]:
    """Fetch source items (real API or demo), skip duplicates, run AI engine, save as pending drafts.
    When allow_duplicates is False (auto-fetch), skip the cycle if nothing new is available
    to avoid re-processing the demo pool and wasting LLM credits."""
    existing = await db.articles.find({}, {"source_title": 1}).to_list(2000)
    used = {d.get("source_title") for d in existing}

    items, source_label = await fetch_source_items(category, count)
    fresh = [n for n in items if n["source_title"] not in used]
    if not fresh:
        if not allow_duplicates:
            logger.info("Auto-fetch: no new articles available, skipping cycle.")
            return []
        fresh = items  # manual fetch may re-process if everything already seen (demo pool small)
    batch = fresh[: max(1, min(count, 10))]

    watermark_text = await get_watermark_text()
    results = await asyncio.gather(*[process_item(item, watermark_text) for item in batch])
    docs = [a.model_dump() for a in results]
    if docs:
        await db.articles.insert_many(docs)
    await db.settings.update_one(
        {"_id": "global"},
        {"$set": {"last_fetch_at": datetime.now(timezone.utc).isoformat(),
                  "last_fetch_source": source_label}},
        upsert=True,
    )
    logger.info(f"Fetched {len(docs)} articles via '{source_label}'.")
    return results


# ----------------------------- Routes -----------------------------
@api_router.get("/")
async def root():
    return {"message": f"{SITE_NAME} AI Engine running", "site_name": SITE_NAME}


@api_router.get("/site")
async def site_info():
    return {"site_name": SITE_NAME}


@api_router.post("/auth/login")
async def login(req: LoginRequest, request: Request):
    email = req.email.lower().strip()
    ident = f"{request.client.host if request.client else 'x'}:{email}"
    attempt = await db.login_attempts.find_one({"_id": ident})
    now = datetime.now(timezone.utc)
    if attempt and attempt.get("count", 0) >= 5:
        locked_until = attempt.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until) > now:
            raise HTTPException(status_code=429, detail="बहुत अधिक प्रयास। 15 मिनट बाद कोशिश करें।")

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"_id": ident},
            {"$inc": {"count": 1},
             "$set": {"locked_until": (now + timedelta(minutes=15)).isoformat()}},
            upsert=True,
        )
        raise HTTPException(status_code=401, detail="ईमेल या पासवर्ड गलत है")

    await db.login_attempts.delete_one({"_id": ident})
    token = create_access_token(email)
    return {"access_token": token, "token_type": "bearer",
            "user": {"email": user["email"], "name": user.get("name", "Admin"), "role": user.get("role", "admin")}}


@api_router.get("/auth/me")
async def auth_me(user: dict = Depends(get_current_user)):
    return user


@api_router.get("/categories")
async def get_categories():
    return CATEGORIES


@api_router.get("/settings", response_model=Settings)
async def read_settings():
    return Settings(watermark_text=await get_watermark_text())


@api_router.put("/settings", response_model=Settings)
async def update_settings(s: Settings, user: dict = Depends(get_current_user)):
    await db.settings.update_one({"_id": "global"},
                                 {"$set": {"watermark_text": s.watermark_text}}, upsert=True)
    return s


@api_router.get("/auto-fetch/status")
async def auto_fetch_status():
    doc = await db.settings.find_one({"_id": "global"}) or {}
    return {
        "enabled": AUTO_FETCH_ENABLED,
        "interval_hours": AUTO_FETCH_INTERVAL_HOURS,
        "count": AUTO_FETCH_COUNT,
        "provider": NEWS_PROVIDER,
        "using_real_api": bool((NEWS_PROVIDER == "gnews" and GNEWS_API_KEY) or (NEWS_PROVIDER == "newsdata" and NEWSDATA_API_KEY)),
        "last_fetch_at": doc.get("last_fetch_at"),
        "last_fetch_source": doc.get("last_fetch_source"),
    }


@api_router.post("/fetch-news", response_model=List[Article])
async def fetch_news(req: FetchRequest, user: dict = Depends(get_current_user)):
    """Fetch fresh foreign news, run AI rewrite + image + watermark, save as pending drafts."""
    return await run_fetch_pipeline(req.count, req.category)


@api_router.post("/manual-upload", response_model=Article)
async def manual_upload(req: ManualUpload, user: dict = Depends(get_current_user)):
    """Admin pastes news text (or a link); run it through the same AI engine and save as a pending draft."""
    title = (req.title or "").strip()
    content = (req.content or "").strip()
    source_name = "मैन्युअल अपलोड"

    if req.url and req.url.strip():
        source_name = req.url.strip()
        if not content:
            fetched_title, fetched_text = fetch_url_text(req.url.strip())
            title = title or fetched_title
            content = fetched_text

    if not content and not title:
        raise HTTPException(status_code=400, detail="कृपया खबर का टेक्स्ट या एक वैध लिंक दें।")

    if not title:
        title = content[:90]
    if not content:
        content = title

    item = {
        "source_title": title,
        "source_content": content,
        "source_name": source_name,
        "category": req.category or "दुनिया",
    }
    watermark_text = await get_watermark_text()
    art = await process_item(item, watermark_text)
    await db.articles.insert_one(art.model_dump())
    return art


@api_router.get("/articles", response_model=List[Article])
async def list_articles(status: Optional[str] = None, category: Optional[str] = None):
    q = {}
    if status:
        q["status"] = status
    if category:
        q["category"] = category
    docs = await db.articles.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return docs


@api_router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    doc = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc


@api_router.put("/articles/{article_id}", response_model=Article)
async def edit_article(article_id: str, edit: EditArticle, user: dict = Depends(get_current_user)):
    update = {k: v for k, v in edit.model_dump().items() if v is not None}
    if update:
        await db.articles.update_one({"id": article_id}, {"$set": update})
    doc = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc


@api_router.post("/articles/{article_id}/approve", response_model=Article)
async def approve_article(article_id: str, user: dict = Depends(get_current_user)):
    await db.articles.update_one(
        {"id": article_id},
        {"$set": {"status": "published", "published_at": datetime.now(timezone.utc).isoformat()}})
    doc = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc


@api_router.post("/articles/{article_id}/reject", response_model=Article)
async def reject_article(article_id: str, user: dict = Depends(get_current_user)):
    await db.articles.update_one({"id": article_id}, {"$set": {"status": "rejected"}})
    doc = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc


@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, user: dict = Depends(get_current_user)):
    await db.articles.delete_one({"id": article_id})
    return {"ok": True}


@api_router.get("/stats")
async def stats():
    return {
        "pending": await db.articles.count_documents({"status": "pending"}),
        "published": await db.articles.count_documents({"status": "published"}),
        "rejected": await db.articles.count_documents({"status": "rejected"}),
    }


async def auto_fetch_loop():
    interval = max(0.05, AUTO_FETCH_INTERVAL_HOURS) * 3600
    while True:
        await asyncio.sleep(interval)
        try:
            logger.info("Auto-fetch cycle starting...")
            await run_fetch_pipeline(AUTO_FETCH_COUNT, None, allow_duplicates=False)
        except Exception as e:
            logger.error(f"Auto-fetch cycle failed: {e}")


async def seed_admin():
    await db.users.create_index("email", unique=True)
    email = ADMIN_EMAIL.lower()
    existing = await db.users.find_one({"email": email})
    if existing is None:
        await db.users.insert_one({
            "email": email,
            "password_hash": hash_password(ADMIN_PASSWORD),
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Admin user seeded.")
    elif not verify_password(ADMIN_PASSWORD, existing["password_hash"]):
        await db.users.update_one({"email": email},
                                  {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}})
        logger.info("Admin password updated from env.")


@app.on_event("startup")
async def seed_data():
    await seed_admin()
    # rebrand old watermark text for display consistency
    await db.articles.update_many({"watermark_text": "MyNews"}, {"$set": {"watermark_text": SITE_NAME}})
    if await db.articles.count_documents({}) == 0:
        for s in SEED_ARTICLES:
            art = Article(
                source_title=s["source_title"],
                source_name=s["source_name"],
                category=s["category"],
                rewritten_headline=s["rewritten_headline"],
                rewritten_article=s["rewritten_article"],
                facts=[Fact(**f) for f in s["facts"]],
                image_prompt=s["image_prompt"],
                image_url=s["image_url"],
                status="published",
                ai_processed=True,
                published_at=datetime.now(timezone.utc).isoformat(),
            )
            await db.articles.insert_one(art.model_dump())
        logger.info("Seeded published demo articles.")

    if AUTO_FETCH_ENABLED:
        asyncio.create_task(auto_fetch_loop())
        logger.info(f"Auto-fetch loop enabled: every {AUTO_FETCH_INTERVAL_HOURS}h, {AUTO_FETCH_COUNT} articles.")


app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
