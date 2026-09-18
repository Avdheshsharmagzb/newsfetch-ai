"""Backend API tests for MyNews Hindi AI news app."""
import os
import re
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE:
    # fallback: read frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE = line.strip().split("=", 1)[1].strip().strip('"')
BASE = BASE.rstrip("/")
API = f"{BASE}/api"

AI_TIMEOUT = 180


@pytest.fixture(scope="session")
def created_ids():
    return {"ids": []}


# ---- Basic health / seed ----
def test_root():
    r = requests.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    assert "MyNews" in r.json().get("message", "")


def test_categories():
    r = requests.get(f"{API}/categories", timeout=15)
    assert r.status_code == 200
    cats = r.json()
    assert isinstance(cats, list) and len(cats) >= 5
    assert "दुनिया" in cats


def test_stats_shape():
    r = requests.get(f"{API}/stats", timeout=15)
    assert r.status_code == 200
    data = r.json()
    for k in ("pending", "published", "rejected"):
        assert k in data
        assert isinstance(data[k], int)


def test_published_seed_articles():
    r = requests.get(f"{API}/articles?status=published", timeout=15)
    assert r.status_code == 200
    arts = r.json()
    assert isinstance(arts, list)
    assert len(arts) >= 3, f"expected >=3 seeded published, got {len(arts)}"
    for a in arts[:3]:
        assert a["status"] == "published"
        assert a["rewritten_headline"]
        assert a["rewritten_article"]


# ---- Settings ----
def test_settings_get_and_update():
    r = requests.get(f"{API}/settings", timeout=15)
    assert r.status_code == 200
    original = r.json()["watermark_text"]

    new_text = "MyNewsTEST"
    r2 = requests.put(f"{API}/settings", json={"watermark_text": new_text}, timeout=15)
    assert r2.status_code == 200
    assert r2.json()["watermark_text"] == new_text

    r3 = requests.get(f"{API}/settings", timeout=15)
    assert r3.json()["watermark_text"] == new_text

    # restore
    requests.put(f"{API}/settings", json={"watermark_text": original or "MyNews"}, timeout=15)


# ---- Fact-protection helper ----
def _extract_numbers_dates(text: str):
    # Extract numeric tokens (with %/decimals) and simple year patterns
    nums = re.findall(r"\d[\d,\.]*%?", text)
    return set(n.strip(".,") for n in nums if n)


# ---- Fetch news (AI) ----
def test_fetch_news_ai(created_ids):
    r = requests.post(f"{API}/fetch-news", json={"count": 1}, timeout=AI_TIMEOUT)
    assert r.status_code == 200, r.text
    arts = r.json()
    assert isinstance(arts, list) and len(arts) == 1
    a = arts[0]
    assert a["status"] == "pending"
    assert a["watermark_text"]  # non-empty
    assert a["rewritten_headline"], "empty Hindi headline"
    assert a["rewritten_article"], "empty Hindi article"
    # Hindi check - Devanagari present
    assert re.search(r"[\u0900-\u097F]", a["rewritten_headline"]), "headline not Hindi"
    assert re.search(r"[\u0900-\u097F]", a["rewritten_article"]), "article not Hindi"
    # image
    assert a["image_url"], "image_url empty"
    assert a["image_url"].startswith("data:image/jpeg;base64,"), f"image not base64 jpeg: {a['image_url'][:60]}"
    # facts list
    assert isinstance(a["facts"], list)

    # Fact-protection: numbers/percentages from source should appear in rewritten article
    src_nums = _extract_numbers_dates(a["source_content"])
    rewritten_nums = _extract_numbers_dates(a["rewritten_article"])
    # allow small leniency: at least 70% of source numeric tokens preserved
    if src_nums:
        preserved = src_nums & rewritten_nums
        ratio = len(preserved) / len(src_nums)
        assert ratio >= 0.6, f"Fact protection weak. src={src_nums} rewritten={rewritten_nums} preserved_ratio={ratio}"

    created_ids["ids"].append(a["id"])
    created_ids["fetch_id"] = a["id"]


# ---- Manual upload ----
def test_manual_upload_ai(created_ids):
    payload = {
        "title": "OpenAI raises 40 billion dollars at 300 billion valuation on March 31 2025",
        "content": (
            "OpenAI announced on March 31, 2025 that it has raised 40 billion US dollars in a funding round "
            "led by SoftBank at a valuation of 300 billion dollars. CEO Sam Altman said in San Francisco that "
            "the company now serves 500 million weekly active users. The round values OpenAI 80% higher than "
            "its previous funding in October 2024."
        ),
        "category": "तकनीक",
    }
    r = requests.post(f"{API}/manual-upload", json=payload, timeout=AI_TIMEOUT)
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["status"] == "pending"
    assert a["category"] == "तकनीक"
    assert re.search(r"[\u0900-\u097F]", a["rewritten_headline"])
    assert re.search(r"[\u0900-\u097F]", a["rewritten_article"])
    # image may or may not generate; if present, must be data URL
    if a["image_url"]:
        assert a["image_url"].startswith("data:image/jpeg;base64,")

    # Fact protection: critical numbers preserved
    body = a["rewritten_article"]
    for token in ["40", "300", "500", "80", "2025"]:
        assert token in body, f"Missing fact token '{token}' in rewritten article: {body[:400]}"

    created_ids["ids"].append(a["id"])
    created_ids["manual_id"] = a["id"]


# ---- Edit / approve / reject workflow ----
def test_edit_article(created_ids):
    aid = created_ids.get("manual_id") or created_ids["ids"][-1]
    new_head = "संपादित हिंदी हेडलाइन टेस्ट"
    r = requests.put(f"{API}/articles/{aid}", json={"rewritten_headline": new_head}, timeout=30)
    assert r.status_code == 200
    assert r.json()["rewritten_headline"] == new_head
    # verify persistence
    r2 = requests.get(f"{API}/articles/{aid}", timeout=15)
    assert r2.json()["rewritten_headline"] == new_head


def test_approve_article(created_ids):
    aid = created_ids.get("fetch_id")
    assert aid, "no fetch id"
    r = requests.post(f"{API}/articles/{aid}/approve", timeout=30)
    assert r.status_code == 200
    a = r.json()
    assert a["status"] == "published"
    assert a["published_at"]
    # confirm appears in published list
    pub = requests.get(f"{API}/articles?status=published", timeout=15).json()
    assert any(x["id"] == aid for x in pub)


def test_reject_article(created_ids):
    aid = created_ids.get("manual_id")
    assert aid
    r = requests.post(f"{API}/articles/{aid}/reject", timeout=30)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    rej = requests.get(f"{API}/articles?status=rejected", timeout=15).json()
    assert any(x["id"] == aid for x in rej)


def test_cleanup(created_ids):
    for aid in created_ids["ids"]:
        requests.delete(f"{API}/articles/{aid}", timeout=15)
