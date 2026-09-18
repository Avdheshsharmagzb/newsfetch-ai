from fastapi import FastAPI, APIRouter, HTTPException
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
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont
from emergentintegrations.llm.chat import LlmChat, UserMessage

from demo_news import DEMO_NEWS, CATEGORIES, SEED_ARTICLES

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

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
    watermark_text: str = "MyNews"
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
    watermark_text: str = "MyNews"


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
    return doc.get("watermark_text", "MyNews") if doc else "MyNews"


# ----------------------------- Routes -----------------------------
@api_router.get("/")
async def root():
    return {"message": "MyNews AI Engine running"}


@api_router.get("/categories")
async def get_categories():
    return CATEGORIES


@api_router.get("/settings", response_model=Settings)
async def read_settings():
    return Settings(watermark_text=await get_watermark_text())


@api_router.put("/settings", response_model=Settings)
async def update_settings(s: Settings):
    await db.settings.update_one({"_id": "global"},
                                 {"$set": {"watermark_text": s.watermark_text}}, upsert=True)
    return s


@api_router.post("/fetch-news", response_model=List[Article])
async def fetch_news(req: FetchRequest):
    """Fetch fresh foreign news (demo pool), run AI rewrite + image + watermark, save as pending drafts."""
    existing = await db.articles.find({}, {"source_title": 1}).to_list(1000)
    used = {d.get("source_title") for d in existing}
    pool = [n for n in DEMO_NEWS if n["source_title"] not in used]
    if req.category:
        pool = [n for n in pool if n["category"] == req.category]
    if not pool:
        pool = [n for n in DEMO_NEWS if n["source_title"] not in used] or DEMO_NEWS[:]
    random.shuffle(pool)
    batch = pool[: max(1, min(req.count, 4))]

    watermark_text = await get_watermark_text()
    results = await asyncio.gather(*[process_item(item, watermark_text) for item in batch])
    docs = [a.model_dump() for a in results]
    if docs:
        await db.articles.insert_many(docs)
    return results


@api_router.post("/manual-upload", response_model=Article)
async def manual_upload(req: ManualUpload):
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
async def edit_article(article_id: str, edit: EditArticle):
    update = {k: v for k, v in edit.model_dump().items() if v is not None}
    if update:
        await db.articles.update_one({"id": article_id}, {"$set": update})
    doc = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc


@api_router.post("/articles/{article_id}/approve", response_model=Article)
async def approve_article(article_id: str):
    await db.articles.update_one(
        {"id": article_id},
        {"$set": {"status": "published", "published_at": datetime.now(timezone.utc).isoformat()}})
    doc = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc


@api_router.post("/articles/{article_id}/reject", response_model=Article)
async def reject_article(article_id: str):
    await db.articles.update_one({"id": article_id}, {"$set": {"status": "rejected"}})
    doc = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc


@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str):
    await db.articles.delete_one({"id": article_id})
    return {"ok": True}


@api_router.get("/stats")
async def stats():
    return {
        "pending": await db.articles.count_documents({"status": "pending"}),
        "published": await db.articles.count_documents({"status": "published"}),
        "rejected": await db.articles.count_documents({"status": "rejected"}),
    }


@app.on_event("startup")
async def seed_data():
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
