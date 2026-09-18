import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, timeAgo, CATEGORY_META } from "@/lib/newsApi";
import { NewsImage } from "@/components/NewsImage";
import { ArrowLeft, ShieldCheck, Loader2 } from "lucide-react";

export default function ArticleDetail() {
  const { id } = useParams();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/articles/${id}`).then((r) => setArticle(r.data)).finally(() => setLoading(false));
  }, [id]);

  if (loading)
    return (
      <div className="min-h-screen flex justify-center items-center bg-[#FAF7F2]">
        <Loader2 className="w-8 h-8 animate-spin text-[#C8102E]" />
      </div>
    );

  if (!article)
    return (
      <div className="min-h-screen flex flex-col justify-center items-center bg-[#FAF7F2] gap-3">
        <p className="text-slate-600">खबर नहीं मिली।</p>
        <Link to="/" className="text-[#C8102E] font-semibold">← होम पर लौटें</Link>
      </div>
    );

  const meta = CATEGORY_META[article.category] || {};

  return (
    <div className="min-h-screen bg-[#FAF7F2]">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <Link
          to="/"
          data-testid="back-home-link"
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-[#C8102E] mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> सभी खबरें
        </Link>

        <span className="text-xs font-mono-j uppercase tracking-[0.2em] font-semibold text-[#C8102E]">
          {meta.emoji} {article.category}
        </span>
        <h1
          data-testid="article-headline"
          className="font-display text-3xl md:text-5xl text-[#121316] leading-snug mt-2"
        >
          {article.rewritten_headline}
        </h1>
        <div className="mt-3 flex items-center gap-3 text-sm text-slate-500 font-mono-j">
          <span>{timeAgo(article.published_at || article.created_at)}</span>
          {article.source_name && <span>· स्रोत: {article.source_name}</span>}
        </div>

        <NewsImage
          src={article.image_url}
          alt={article.rewritten_headline}
          watermark={article.watermark_text}
          showFactShield={article.ai_processed}
          className="h-64 md:h-96 rounded-lg mt-6"
        />

        {article.facts?.length > 0 && (
          <div
            data-testid="fact-shield-badge"
            className="mt-6 bg-emerald-50 border border-emerald-200 rounded-lg p-4"
          >
            <div className="flex items-center gap-2 text-emerald-800 font-semibold mb-2">
              <ShieldCheck className="w-5 h-5" /> तथ्य सुरक्षा — ये तथ्य मूल स्रोत जैसे ही हैं
            </div>
            <div className="flex flex-wrap gap-2">
              {article.facts.map((f, i) => (
                <span
                  key={i}
                  className="bg-white border border-emerald-200 text-emerald-800 text-xs font-mono-j px-2.5 py-1 rounded-full"
                >
                  <span className="opacity-60">{f.type}:</span> {f.value}
                </span>
              ))}
            </div>
          </div>
        )}

        <article
          data-testid="article-body"
          className="mt-6 text-lg leading-relaxed text-slate-800 whitespace-pre-line"
        >
          {article.rewritten_article}
        </article>
      </div>
    </div>
  );
}
