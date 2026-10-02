import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import {
  Newspaper, Download, Loader2, Check, X, ShieldCheck, Sparkles,
  Settings, Clock, CheckCircle2, XCircle, Save, ArrowRight, Upload, Zap, LogOut, ImagePlus,
} from "lucide-react";
import { api, CATEGORY_META, timeAgo, SITE_NAME } from "@/lib/newsApi";
import { NewsImage } from "@/components/NewsImage";
import { useAuth } from "@/context/AuthContext";

const TABS = [
  { key: "pending", label: "समीक्षा हेतु लंबित", icon: Clock, color: "text-amber-400" },
  { key: "published", label: "प्रकाशित", icon: CheckCircle2, color: "text-emerald-400" },
  { key: "rejected", label: "अस्वीकृत", icon: XCircle, color: "text-rose-400" },
];

export default function Admin() {
  const { logout } = useAuth();
  const [tab, setTab] = useState("pending");
  const [articles, setArticles] = useState([]);
  const [stats, setStats] = useState({ pending: 0, published: 0, rejected: 0 });
  const [categories, setCategories] = useState([]);
  const [fetching, setFetching] = useState(false);
  const [loading, setLoading] = useState(true);
  const [fetchCat, setFetchCat] = useState("");
  const [watermark, setWatermark] = useState("Ghaziabad Times");
  const [showSettings, setShowSettings] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [form, setForm] = useState({ title: "", content: "", url: "", category: "दुनिया", image_base64: "" });
  const [autoStatus, setAutoStatus] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [a, s] = await Promise.all([
        api.get("/articles", { params: { status: tab } }),
        api.get("/stats"),
      ]);
      setArticles(a.data);
      setStats(s.data);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    api.get("/categories").then((r) => setCategories(r.data));
    api.get("/settings").then((r) => setWatermark(r.data.watermark_text));
    api.get("/auto-fetch/status").then((r) => setAutoStatus(r.data)).catch(() => {});
  }, []);

  const fetchNews = async () => {
    setFetching(true);
    toast.loading("खबरें फेच हो रही हैं और AI इनका हिंदी रीराइट + इमेज बना रहा है...", { id: "fetch" });
    try {
      const r = await api.post("/fetch-news", { count: 3, category: fetchCat || null });
      toast.success(`${r.data.length} नई खबरें तैयार हैं — समीक्षा करें`, { id: "fetch" });
      setTab("pending");
      await refresh();
    } catch (e) {
      toast.error("फेच में समस्या आई। दोबारा कोशिश करें।", { id: "fetch" });
    } finally {
      setFetching(false);
    }
  };

  const saveWatermark = async () => {
    await api.put("/settings", { watermark_text: watermark || "Ghaziabad Times" });
    toast.success("वाटरमार्क सेटिंग सहेजी गई");
    setShowSettings(false);
  };

  const onPickPhoto = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) { toast.error("कृपया एक इमेज फ़ाइल चुनें"); return; }
    if (file.size > 8 * 1024 * 1024) { toast.error("फोटो 8MB से छोटी होनी चाहिए"); return; }
    const reader = new FileReader();
    reader.onload = () => setForm((f) => ({ ...f, image_base64: reader.result }));
    reader.readAsDataURL(file);
  };

  const submitUpload = async () => {
    if (!form.content.trim() && !form.url.trim()) {
      toast.error("कृपया खबर का टेक्स्ट पेस्ट करें या एक लिंक दें।");
      return;
    }
    setUploading(true);
    toast.loading("आपकी खबर AI इंजन से प्रोसेस हो रही है (हिंदी रीराइट + इमेज + वाटरमार्क)...", { id: "upload" });
    try {
      await api.post("/manual-upload", form);
      toast.success("खबर प्रोसेस होकर 'लंबित' सूची में जुड़ गई", { id: "upload" });
      setShowUpload(false);
      setForm({ title: "", content: "", url: "", category: "दुनिया", image_base64: "" });
      setTab("pending");
      await refresh();
    } catch (e) {
      const msg = e?.response?.data?.detail || "अपलोड विफल। दोबारा कोशिश करें।";
      toast.error(msg, { id: "upload" });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F1117] text-slate-100">
      {/* Command header */}
      <header className="bg-[#181B24] border-b border-[#2B303E] sticky top-0 z-40">
        <div className="max-w-[1500px] mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4 flex-wrap">
          <Link to="/" className="flex items-center gap-2" data-testid="admin-logo">
            <Newspaper className="w-6 h-6 text-[#C8102E]" />
            <span className="font-display text-2xl">{SITE_NAME}</span>
            <span className="text-[10px] font-mono-j uppercase tracking-[0.2em] text-slate-500 border-l border-[#2B303E] pl-2">
              कंट्रोल पैनल
            </span>
          </Link>

          <div className="flex items-center gap-2 flex-wrap">
            <select
              data-testid="fetch-category-select"
              value={fetchCat}
              onChange={(e) => setFetchCat(e.target.value)}
              className="bg-[#0F1117] border border-[#2B303E] rounded-md text-sm px-3 py-2 text-slate-200"
            >
              <option value="">सभी श्रेणियाँ</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <button
              onClick={() => setShowUpload(true)}
              data-testid="manual-upload-btn"
              className="flex items-center gap-2 bg-[#232833] hover:bg-[#2B303E] border border-[#C8102E]/40 text-sm font-semibold px-4 py-2 rounded-md transition-colors"
            >
              <Upload className="w-4 h-4 text-[#C8102E]" /> मैन्युअल अपलोड
            </button>
            <button
              onClick={fetchNews}
              disabled={fetching}
              data-testid="fetch-news-btn"
              className="flex items-center gap-2 bg-[#C8102E] hover:bg-[#A00C23] disabled:opacity-60 text-white text-sm font-semibold px-4 py-2 rounded-md transition-colors"
            >
              {fetching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              खबरें फेच करें
            </button>
            <button
              onClick={() => setShowSettings(true)}
              data-testid="watermark-settings-btn"
              className="flex items-center gap-2 bg-[#232833] hover:bg-[#2B303E] text-sm font-semibold px-3 py-2 rounded-md"
            >
              <Settings className="w-4 h-4" /> वाटरमार्क
            </button>
            <Link to="/" className="text-sm text-slate-400 hover:text-white px-2" data-testid="view-site-link">
              साइट देखें ↗
            </Link>
            <button
              onClick={() => { logout(); window.location.href = "/control-login"; }}
              data-testid="logout-btn"
              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-rose-400 px-2"
            >
              <LogOut className="w-4 h-4" /> लॉगआउट
            </button>
          </div>
        </div>
        {autoStatus?.enabled && (
          <div className="max-w-[1500px] mx-auto px-4 sm:px-6 pb-2">
            <div
              data-testid="auto-fetch-badge"
              className="inline-flex items-center gap-2 text-xs font-mono-j text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-full px-3 py-1"
            >
              <Zap className="w-3.5 h-3.5" />
              ऑटो-फेच चालू · हर {autoStatus.interval_hours} घंटे · {autoStatus.count} खबरें ·
              {autoStatus.using_real_api ? ` लाइव ${autoStatus.provider.toUpperCase()}` : " डेमो डेटा (API key जोड़ें)"}
              {autoStatus.last_fetch_at && ` · पिछली बार: ${timeAgo(autoStatus.last_fetch_at)}`}
            </div>
          </div>
        )}
      </header>

      <main className="max-w-[1500px] mx-auto px-4 sm:px-6 py-6">
        {/* stats + tabs */}
        <div className="flex gap-3 mb-6 flex-wrap">
          {TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                data-testid={`tab-${t.key}`}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-semibold transition-colors ${
                  tab === t.key
                    ? "bg-[#181B24] border-[#C8102E] text-white"
                    : "bg-[#12151C] border-[#2B303E] text-slate-400 hover:text-white"
                }`}
              >
                <Icon className={`w-4 h-4 ${t.color}`} />
                {t.label}
                <span className="font-mono-j bg-[#0F1117] px-2 py-0.5 rounded text-xs">
                  {stats[t.key]}
                </span>
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="flex justify-center py-32">
            <Loader2 className="w-8 h-8 animate-spin text-[#C8102E]" />
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-32 text-slate-500" data-testid="admin-empty">
            <Sparkles className="w-10 h-10 mx-auto mb-3 text-slate-600" />
            <p>यहाँ कोई खबर नहीं है।</p>
            {tab === "pending" && <p className="text-sm mt-1">ऊपर "खबरें फेच करें" दबाएं।</p>}
          </div>
        ) : (
          <div className="space-y-5">
            <AnimatePresence>
              {articles.map((a) => (
                <ReviewCard key={a.id} article={a} tab={tab} onChange={refresh} />
              ))}
            </AnimatePresence>
          </div>
        )}
      </main>

      {/* manual upload modal */}
      {showUpload && (
        <div
          className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
          onClick={() => !uploading && setShowUpload(false)}
        >
          <div
            className="bg-[#181B24] border border-[#2B303E] rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
            data-testid="manual-upload-modal"
          >
            <div className="flex items-center gap-2 mb-1">
              <Upload className="w-5 h-5 text-[#C8102E]" />
              <h3 className="font-display text-2xl">मैन्युअल न्यूज़ अपलोड</h3>
            </div>
            <p className="text-sm text-slate-400 mb-5">
              किसी भी स्रोत से खबर का टेक्स्ट यहाँ पेस्ट करें या लिंक दें। AI इंजन इसे आकर्षक हिंदी हेडलाइन,
              व्याकरण-शुद्ध लेख (तथ्य सुरक्षित) और वाटरमार्क इमेज में बदल देगा।
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
              <div>
                <label className="text-xs font-mono-j text-slate-400 uppercase tracking-wider">शीर्षक (वैकल्पिक)</label>
                <input
                  data-testid="upload-title-input"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="मूल खबर का शीर्षक"
                  className="mt-1 w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2 text-slate-100"
                />
              </div>
              <div>
                <label className="text-xs font-mono-j text-slate-400 uppercase tracking-wider">श्रेणी</label>
                <select
                  data-testid="upload-category-select"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="mt-1 w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2 text-slate-100"
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            <label className="text-xs font-mono-j text-slate-400 uppercase tracking-wider">खबर का टेक्स्ट (कॉपी-पेस्ट)</label>
            <textarea
              data-testid="upload-content-input"
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              rows={8}
              placeholder="यहाँ खबर का पूरा टेक्स्ट पेस्ट करें..."
              className="mt-1 w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2 text-sm text-slate-200 leading-relaxed resize-y"
            />

            <div className="mt-3">
              <label className="text-xs font-mono-j text-slate-400 uppercase tracking-wider">या खबर का लिंक (वैकल्पिक)</label>
              <input
                data-testid="upload-url-input"
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value })}
                placeholder="https://example.com/news-article"
                className="mt-1 w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2 text-slate-100 font-mono-j text-sm"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                लिंक देने पर सिस्टम पेज से टेक्स्ट निकालने की कोशिश करेगा (कुछ साइट्स ब्लॉक कर सकती हैं — तब टेक्स्ट पेस्ट करें)।
              </p>
            </div>

            <div className="mt-3">
              <label className="text-xs font-mono-j text-slate-400 uppercase tracking-wider">अपनी फोटो (वैकल्पिक)</label>
              {form.image_base64 ? (
                <div className="mt-1 flex items-center gap-3">
                  <div className="relative">
                    <img
                      src={form.image_base64}
                      alt="preview"
                      data-testid="upload-photo-preview"
                      className="w-28 h-20 object-cover rounded-md border border-[#2B303E]"
                    />
                    <span className="absolute bottom-1 right-1 bg-[#C8102E]/90 text-white text-[8px] font-mono-j px-1 rounded-sm">
                      Ghaziabad Times
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, image_base64: "" }))}
                    data-testid="remove-photo-btn"
                    className="text-xs text-rose-400 hover:text-rose-300 font-semibold"
                  >
                    हटाएँ
                  </button>
                </div>
              ) : (
                <label
                  data-testid="upload-photo-label"
                  className="mt-1 flex items-center gap-2 cursor-pointer bg-[#0F1117] border border-dashed border-[#2B303E] hover:border-[#C8102E] rounded-md px-3 py-2.5 text-sm text-slate-400 w-fit"
                >
                  <ImagePlus className="w-4 h-4 text-[#C8102E]" /> फोटो चुनें
                  <input type="file" accept="image/*" onChange={onPickPhoto} className="hidden" data-testid="upload-photo-input" />
                </label>
              )}
              <p className="text-[11px] text-slate-500 mt-1">
                फोटो दें तो उस पर अपने-आप "Ghaziabad Times" वाटरमार्क लगेगा। फोटो न दें तो AI अपने-आप इमेज बना देगा।
              </p>
            </div>

            <div className="flex justify-end gap-2 mt-5">
              <button
                onClick={() => setShowUpload(false)}
                disabled={uploading}
                className="px-4 py-2 rounded-md bg-[#232833] text-sm"
              >
                रद्द करें
              </button>
              <button
                onClick={submitUpload}
                disabled={uploading}
                data-testid="submit-upload-btn"
                className="flex items-center gap-2 px-5 py-2 rounded-md bg-[#C8102E] hover:bg-[#A00C23] disabled:opacity-60 text-sm font-semibold"
              >
                {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                AI से प्रोसेस करें
              </button>
            </div>
          </div>
        </div>
      )}

      {/* watermark settings modal */}
      {showSettings && (
        <div
          className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
          onClick={() => setShowSettings(false)}
        >
          <div
            className="bg-[#181B24] border border-[#2B303E] rounded-xl p-6 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="font-display text-2xl mb-1">वाटरमार्क सेटिंग</h3>
            <p className="text-sm text-slate-400 mb-4">
              यह टेक्स्ट नई फेच की गई AI इमेज पर लगेगा।
            </p>
            <input
              data-testid="watermark-text-input"
              value={watermark}
              onChange={(e) => setWatermark(e.target.value)}
              className="w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2 text-slate-100 font-mono-j"
            />
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2 rounded-md bg-[#232833] text-sm"
              >
                रद्द करें
              </button>
              <button
                onClick={saveWatermark}
                data-testid="save-watermark-btn"
                className="flex items-center gap-2 px-4 py-2 rounded-md bg-[#C8102E] hover:bg-[#A00C23] text-sm font-semibold"
              >
                <Save className="w-4 h-4" /> सहेजें
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ReviewCard({ article, tab, onChange }) {
  const [headline, setHeadline] = useState(article.rewritten_headline);
  const [body, setBody] = useState(article.rewritten_article);
  const [busy, setBusy] = useState(false);
  const meta = CATEGORY_META[article.category] || {};
  const dirty = headline !== article.rewritten_headline || body !== article.rewritten_article;

  const act = async (action) => {
    setBusy(true);
    try {
      if (action === "save") {
        await api.put(`/articles/${article.id}`, { rewritten_headline: headline, rewritten_article: body });
        toast.success("बदलाव सहेजे गए");
      } else if (action === "approve") {
        if (dirty) await api.put(`/articles/${article.id}`, { rewritten_headline: headline, rewritten_article: body });
        await api.post(`/articles/${article.id}/approve`);
        toast.success("खबर प्रकाशित कर दी गई ✓");
      } else if (action === "reject") {
        await api.post(`/articles/${article.id}/reject`);
        toast.success("खबर अस्वीकृत");
      }
      onChange();
    } catch {
      toast.error("कार्रवाई विफल");
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className="bg-[#181B24] border border-[#2B303E] rounded-xl overflow-hidden"
      data-testid={`review-card-${article.id}`}
    >
      <div className="flex items-center justify-between px-5 py-3 border-b border-[#2B303E] bg-[#12151C]">
        <div className="flex items-center gap-2 text-xs font-mono-j">
          <span className="text-[#C8102E] uppercase tracking-wider">{meta.emoji} {article.category}</span>
          <span className="text-slate-500">· {article.source_name}</span>
          <span className="text-slate-600">· {timeAgo(article.created_at)}</span>
        </div>
        {article.ai_processed && (
          <span className="flex items-center gap-1 text-xs text-amber-400 font-mono-j">
            <Sparkles className="w-3 h-3" /> AI प्रोसेस्ड
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
        {/* Original (English source) */}
        <div className="p-5 border-b lg:border-b-0 lg:border-r border-[#2B303E] bg-rose-950/10">
          <div className="text-[10px] font-mono-j uppercase tracking-[0.2em] text-rose-400 mb-2">
            मूल खबर (English Source)
          </div>
          <h4 className="text-slate-200 font-semibold leading-snug">{article.source_title}</h4>
          <p className="mt-2 text-sm text-slate-400 leading-relaxed line-clamp-6">
            {article.source_content}
          </p>
        </div>

        {/* Rewritten (editable Hindi) */}
        <div className="p-5 bg-emerald-950/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono-j uppercase tracking-[0.2em] text-emerald-400">
              AI रीराइट (हिंदी · संपादन योग्य)
            </span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
          </div>
          {tab === "pending" ? (
            <>
              <input
                data-testid="edit-rewritten-headline-input"
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                className="w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2 font-display text-lg text-white leading-snug focus:border-emerald-500 outline-none"
              />
              <textarea
                data-testid="edit-rewritten-article-input"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={6}
                className="mt-2 w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2 text-sm text-slate-200 leading-relaxed focus:border-emerald-500 outline-none resize-y"
              />
            </>
          ) : (
            <>
              <h4 className="font-display text-lg text-white leading-snug">{article.rewritten_headline}</h4>
              <p className="mt-2 text-sm text-slate-300 leading-relaxed line-clamp-6">
                {article.rewritten_article}
              </p>
            </>
          )}
        </div>
      </div>

      {/* facts + image + actions */}
      <div className="px-5 py-4 border-t border-[#2B303E] flex flex-col lg:flex-row gap-4 lg:items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-1 text-xs text-emerald-400 font-mono-j mb-2">
            <ShieldCheck className="w-3.5 h-3.5" /> तथ्य सुरक्षा — मूल जैसे ही
          </div>
          <div className="flex flex-wrap gap-1.5">
            {article.facts?.length ? article.facts.map((f, i) => (
              <span key={i} className="bg-emerald-950/50 border border-emerald-800 text-emerald-300 text-[11px] font-mono-j px-2 py-0.5 rounded">
                {f.type}: {f.value}
              </span>
            )) : <span className="text-xs text-slate-500">कोई तथ्य निकाला नहीं गया</span>}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <NewsImage
            src={article.image_url}
            alt="preview"
            watermark={article.watermark_text}
            className="w-28 h-20 rounded-md shrink-0"
          />
          {tab === "pending" ? (
            <div className="flex flex-col gap-2">
              {dirty && (
                <button
                  onClick={() => act("save")}
                  disabled={busy}
                  data-testid={`save-article-btn-${article.id}`}
                  className="flex items-center gap-1.5 bg-[#232833] hover:bg-[#2B303E] text-xs font-semibold px-3 py-1.5 rounded-md"
                >
                  <Save className="w-3.5 h-3.5" /> सहेजें
                </button>
              )}
              <button
                onClick={() => act("approve")}
                disabled={busy}
                data-testid={`approve-article-btn-${article.id}`}
                className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold px-4 py-2 rounded-md"
              >
                <Check className="w-4 h-4" /> प्रकाशित करें
              </button>
              <button
                onClick={() => act("reject")}
                disabled={busy}
                data-testid={`reject-article-btn-${article.id}`}
                className="flex items-center gap-1.5 bg-[#232833] hover:bg-rose-900/40 text-rose-300 text-sm font-semibold px-4 py-2 rounded-md"
              >
                <X className="w-4 h-4" /> अस्वीकार
              </button>
            </div>
          ) : (
            <span className={`text-sm font-semibold ${tab === "published" ? "text-emerald-400" : "text-rose-400"}`}>
              {tab === "published" ? "✓ लाइव" : "अस्वीकृत"}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
