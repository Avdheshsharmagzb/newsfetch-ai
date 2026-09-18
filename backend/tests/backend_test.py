"""Backend API tests for MyNews Hindi AI news app - iteration 2 (auth + auto-fetch)."""
import os
import re
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE = line.strip().split("=", 1)[1].strip().strip('"')
BASE = BASE.rstrip("/")
API = f"{BASE}/api"

ADMIN_EMAIL = "admin@mynews.com"
ADMIN_PASSWORD = "Admin@12345"
AI_TIMEOUT = 180


# --------------------- Fixtures ---------------------
@pytest.fixture(scope="session")
def created_ids():
    return {"ids": []}


@pytest.fixture(scope="session")
def admin_token():
    # Clear any prior lockout by hitting DB-independent path: just try login. If locked, skip.
    r = requests.post(f"{API}/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# --------------------- Basic / seed ---------------------
def test_root():
    r = requests.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    assert "MyNews" in r.json().get("message", "")


def test_categories_public():
    r = requests.get(f"{API}/categories", timeout=15)
    assert r.status_code == 200
    cats = r.json()
    assert isinstance(cats, list) and "दुनिया" in cats


def test_stats_public():
    r = requests.get(f"{API}/stats", timeout=15)
    assert r.status_code == 200
    for k in ("pending", "published", "rejected"):
        assert k in r.json()


def test_public_articles_open():
    r = requests.get(f"{API}/articles?status=published", timeout=15)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_public_settings_open():
    r = requests.get(f"{API}/settings", timeout=15)
    assert r.status_code == 200
    assert "watermark_text" in r.json()


# --------------------- AUTH ---------------------
def test_login_success():
    r = requests.post(f"{API}/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["token_type"] == "bearer"
    assert isinstance(d["access_token"], str) and len(d["access_token"]) > 20
    assert d["user"]["email"] == ADMIN_EMAIL
    assert d["user"]["role"] == "admin"


def test_login_wrong_password_401():
    # use uniquely-cased email so lockout counter is separate from other tests
    r = requests.post(f"{API}/auth/login",
                      json={"email": "wrongtest@mynews.com", "password": "nope"}, timeout=15)
    assert r.status_code == 401


def test_login_lockout_429():
    email = "lockout_probe@mynews.com"
    last = None
    for _ in range(7):
        last = requests.post(f"{API}/auth/login",
                             json={"email": email, "password": "bad"}, timeout=15)
    # after 5+ failures we expect 429
    assert last.status_code == 429, f"expected 429 lockout, got {last.status_code}: {last.text}"


def test_auth_me_requires_token():
    r = requests.get(f"{API}/auth/me", timeout=15)
    assert r.status_code == 401


def test_auth_me_with_token(auth_headers):
    r = requests.get(f"{API}/auth/me", headers=auth_headers, timeout=15)
    assert r.status_code == 200
    assert r.json()["email"] == ADMIN_EMAIL


# --------------------- Protection matrix ---------------------
PROTECTED = [
    ("POST", "/fetch-news", {"count": 1}),
    ("POST", "/manual-upload", {"title": "x", "content": "y"}),
    ("PUT", "/articles/does-not-exist", {"rewritten_headline": "x"}),
    ("POST", "/articles/does-not-exist/approve", None),
    ("POST", "/articles/does-not-exist/reject", None),
    ("DELETE", "/articles/does-not-exist", None),
    ("PUT", "/settings", {"watermark_text": "x"}),
]


@pytest.mark.parametrize("method,path,body", PROTECTED)
def test_protected_without_token_returns_401(method, path, body):
    r = requests.request(method, f"{API}{path}", json=body, timeout=20)
    assert r.status_code == 401, f"{method} {path} -> {r.status_code}"


# --------------------- Auto-fetch status ---------------------
def test_auto_fetch_status():
    r = requests.get(f"{API}/auto-fetch/status", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["enabled"] is True
    assert d["interval_hours"] == 1
    assert d["count"] == 10
    assert d["provider"] == "gnews"
    assert d["using_real_api"] is False  # key empty -> demo


# --------------------- Settings (auth) ---------------------
def test_settings_update_requires_auth_and_persists(auth_headers):
    orig = requests.get(f"{API}/settings", timeout=15).json()["watermark_text"]
    # no token -> 401
    r0 = requests.put(f"{API}/settings", json={"watermark_text": "NO_AUTH"}, timeout=15)
    assert r0.status_code == 401
    # with token
    r1 = requests.put(f"{API}/settings", json={"watermark_text": "MyNewsTEST"},
                      headers=auth_headers, timeout=15)
    assert r1.status_code == 200 and r1.json()["watermark_text"] == "MyNewsTEST"
    # persistence
    assert requests.get(f"{API}/settings").json()["watermark_text"] == "MyNewsTEST"
    # restore
    requests.put(f"{API}/settings", json={"watermark_text": orig or "MyNews"},
                 headers=auth_headers, timeout=15)


# --------------------- AI: fetch-news (demo fallback) ---------------------
def _extract_numbers_dates(text: str):
    nums = re.findall(r"\d[\d,\.]*%?", text)
    return set(n.strip(".,") for n in nums if n)


def test_fetch_news_with_token_demo(auth_headers, created_ids):
    r = requests.post(f"{API}/fetch-news", json={"count": 1},
                      headers=auth_headers, timeout=AI_TIMEOUT)
    assert r.status_code == 200, r.text
    arts = r.json()
    assert isinstance(arts, list) and len(arts) == 1
    a = arts[0]
    assert a["status"] == "pending"
    assert a["watermark_text"]
    assert re.search(r"[\u0900-\u097F]", a["rewritten_headline"])
    assert re.search(r"[\u0900-\u097F]", a["rewritten_article"])
    assert a["image_url"].startswith("data:image/jpeg;base64,")
    src_nums = _extract_numbers_dates(a["source_content"])
    if src_nums:
        preserved = src_nums & _extract_numbers_dates(a["rewritten_article"])
        assert len(preserved) / len(src_nums) >= 0.6
    created_ids["ids"].append(a["id"])
    created_ids["fetch_id"] = a["id"]

    # confirm status endpoint updated
    st = requests.get(f"{API}/auto-fetch/status").json()
    assert st["last_fetch_source"] == "demo"
    assert st["last_fetch_at"]


# --------------------- Manual upload (auth) ---------------------
def test_manual_upload_with_token(auth_headers, created_ids):
    payload = {
        "title": "TEST OpenAI raises 40 billion at 300 billion valuation on March 31 2025",
        "content": (
            "OpenAI announced on March 31, 2025 that it has raised 40 billion US dollars "
            "led by SoftBank at a valuation of 300 billion dollars. The company now serves "
            "500 million weekly active users, 80% higher than October 2024."
        ),
        "category": "तकनीक",
    }
    r = requests.post(f"{API}/manual-upload", json=payload,
                      headers=auth_headers, timeout=AI_TIMEOUT)
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["status"] == "pending" and a["category"] == "तकनीक"
    body = a["rewritten_article"]
    for token in ["40", "300", "500", "80", "2025"]:
        assert token in body, f"missing fact '{token}' in {body[:400]}"
    created_ids["ids"].append(a["id"])
    created_ids["manual_id"] = a["id"]


# --------------------- Edit / approve / reject ---------------------
def test_edit_article_auth(auth_headers, created_ids):
    aid = created_ids.get("manual_id") or created_ids["ids"][-1]
    # unauth
    r0 = requests.put(f"{API}/articles/{aid}", json={"rewritten_headline": "x"}, timeout=15)
    assert r0.status_code == 401
    new_head = "संपादित हिंदी हेडलाइन टेस्ट"
    r = requests.put(f"{API}/articles/{aid}", json={"rewritten_headline": new_head},
                     headers=auth_headers, timeout=30)
    assert r.status_code == 200 and r.json()["rewritten_headline"] == new_head
    assert requests.get(f"{API}/articles/{aid}").json()["rewritten_headline"] == new_head


def test_approve_article_auth(auth_headers, created_ids):
    aid = created_ids["fetch_id"]
    r = requests.post(f"{API}/articles/{aid}/approve", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    a = r.json()
    assert a["status"] == "published" and a["published_at"]


def test_reject_article_auth(auth_headers, created_ids):
    aid = created_ids["manual_id"]
    r = requests.post(f"{API}/articles/{aid}/reject", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_cleanup(auth_headers, created_ids):
    for aid in created_ids["ids"]:
        requests.delete(f"{API}/articles/{aid}", headers=auth_headers, timeout=15)
