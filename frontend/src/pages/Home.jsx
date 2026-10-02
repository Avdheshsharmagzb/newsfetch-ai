import { useEffect, useState } from "react";
import { api, PER_PAGE, NUM_PAGES, SITE_NAME } from "@/lib/newsApi";
import { PublicHeader } from "@/components/PublicHeader";
import { NewsCard } from "@/components/NewsCard";
import { Newspaper, Loader2 } from "lucide-react";

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get("/articles", { params: { status: "published" } })
      .then((r) => setArticles(r.data))
      .finally(() => setLoading(false));
  }, []);

  // auto-distribute by recency: page 1 = newest PER_PAGE, then overflow to 2,3,4
  const start = (page - 1) * PER_PAGE;
  const pageArticles = articles.slice(start, start + PER_PAGE);
  const [feature, ...rest] = page === 1 ? pageArticles : [null, ...pageArticles];

  return (
    <div className="min-h-screen bg-[#FAF7F2]">
      <PublicHeader activePage={page} onPage={setPage} />

      <main className="max-w-7xl mx-auto px-4 sm:px-8 py-8">
        {loading ? (
          <div className="flex justify-center py-32">
            <Loader2 className="w-8 h-8 animate-spin text-[#C8102E]" />
          </div>
        ) : pageArticles.length === 0 ? (
          <div className="text-center py-32" data-testid="empty-state">
            <Newspaper className="w-12 h-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500">पेज {page} पर अभी कोई खबर नहीं है।</p>
          </div>
        ) : (
          <>
            <div className="flex items-baseline justify-between mb-5 border-b-2 border-[#C8102E]/20 pb-2">
              <h2 className="font-display text-2xl md:text-3xl text-[#121316]">पेज {page}</h2>
              <span className="text-xs font-mono-j text-slate-500">
                {pageArticles.length} खबरें
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8" data-testid="news-grid">
              {page === 1 && feature && <NewsCard article={feature} feature index={0} />}
              {rest.filter(Boolean).map((a, i) => (
                <NewsCard key={a.id} article={a} index={i + 1} />
              ))}
            </div>
          </>
        )}
      </main>

      <footer className="border-t-2 border-[#121316] mt-12 py-8 text-center text-sm text-slate-500">
        <p className="font-rozha text-3xl text-[#121316]">{SITE_NAME}</p>
        <p className="mt-1">विश्वसनीय हिंदी समाचार · तथ्य सुरक्षा के साथ</p>
        <div className="mt-3 flex justify-center gap-3 text-xs">
          {Array.from({ length: NUM_PAGES }, (_, i) => i + 1).map((p) => (
            <button key={p} onClick={() => { setPage(p); window.scrollTo(0, 0); }} className="hover:text-[#C8102E]">
              पेज {p}
            </button>
          ))}
        </div>
      </footer>
    </div>
  );
}
