# MyNews — AI हिंदी न्यूज़ इंजन (PRD)

## Original Problem Statement
Automated news web app. **Part 1**: फ्री News API से खबरें फेच → हेडलाइन को आकर्षक/क्लिकेबल हिंदी में रीराइट → आर्टिकल को व्याकरण-शुद्ध हिंदी में रीराइट **बिना तथ्य बदले** (नाम, स्थान, संख्यात्मक आँकड़े, तारीख़, समय ज्यों-के-त्यों) → मूल इमेज की जगह AI इमेज + वेबसाइट नाम का वाटरमार्क। **Part 2**: Admin Dashboard में Manual Upload — खुद टेक्स्ट/लिंक पेस्ट → वही AI इंजन → Pending/Draft लिस्ट। Approval के बाद ही पब्लिश।

## User Choices
- भाषा: विदेशी (अंग्रेज़ी) खबरें → हिंदी आउटपुट; category selection; approval-then-publish workflow.
- News source: DEMO/sample data (कोई API key नहीं) — **MOCKED**.
- Rewrite LLM: OpenAI GPT-5.4 (Emergent Universal Key).
- Image: Gemini Nano Banana (gemini-3.1-flash-image-preview) + Pillow watermark.
- Watermark text: "MyNews" (dashboard से बदल सकते हैं).
- No authentication.

## Architecture
- Backend: FastAPI + MongoDB (motor). AI: emergentintegrations LlmChat. Watermark: Pillow.
  - `/api/fetch-news`, `/api/manual-upload`, `/api/articles` (+status/category filter), `/api/articles/{id}` GET/PUT, `/approve`, `/reject`, DELETE, `/api/stats`, `/api/settings`, `/api/categories`.
  - `process_item()` = ai_rewrite (GPT-5.4, strict fact-protection JSON) + ai_generate_image (Nano Banana) + add_watermark (Pillow, baked JPEG data URL).
  - Startup seeds 3 published Hindi articles.
- Frontend: React + Tailwind + framer-motion + sonner.
  - Public: `/` (Home newspaper feed, category tabs), `/article/:id` (detail with Fact Shield).
  - Admin: `/admin` (fetch, manual upload modal, pending/published/rejected tabs, review card with English-source vs Hindi-rewrite + editable fields, approve/reject, watermark settings).

## Personas
- पाठक: सत्यापित, अच्छी हिंदी में विदेशी खबरें पढ़ना।
- एडमिन/संपादक: AI ड्राफ्ट की समीक्षा, संपादन और approval के बाद प्रकाशन।

## Implemented (2026-06-18)
- Part 1 News fetch (demo) → GPT-5.4 Hindi rewrite with fact-protection → Nano Banana image + MyNews watermark. ✅ tested (fact-preservation verified).
- Part 2 Admin Manual Upload (paste text / link) → same AI engine → Pending draft. ✅ tested.
- Approval workflow (pending → published → public site), reject, edit, watermark settings, category filter. ✅ tested 100%.

## Backlog
- P1: Real free News API integration (GNews/NewsData) replacing demo data when key available.
- P1: Move sync URL-fetch + Pillow work to executor (avoid event-loop block).
- P2: Auth for admin, pagination, scheduled auto-fetch, bookmark/share, dark mode toggle for public site.

## Next Tasks
- Await user feedback; likely add real News API + admin auth.
