import { useEffect, useState } from "react";
import { api } from "@/lib/newsApi";
import { PublicHeader } from "@/components/PublicHeader";
import { NewsCard } from "@/components/NewsCard";
import { Newspaper, Loader2 } from "lucide-react";

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [active, setActive] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async (cat) => {
    setLoading(true);
    try {
      const params = { status: "published" };
      if (cat) params.category = cat;
      const [a, c] = await Promise.all([
        api.get("/articles", { params }),
        categories.length ? Promise.resolve({ data: categories }) : api.get("/categories"),
      ]);
      setArticles(a.data);
      if (!categories.length) setCategories(c.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(active); /* eslint-disable-next-line */ }, [active]);

  const [feature, ...rest] = articles;

  return (
    <div className="min-h-screen bg-[#FAF7F2]">
      <PublicHeader categories={categories} active={active} onCategory={setActive} />

      <main className="max-w-7xl mx-auto px-4 sm:px-8 py-8">
        {loading ? (
          <div className="flex justify-center py-32">
            <Loader2 className="w-8 h-8 animate-spin text-[#C8102E]" />
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-32" data-testid="empty-state">
            <Newspaper className="w-12 h-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500">इस श्रेणी में अभी कोई प्रकाशित खबर नहीं है।</p>
            <p className="text-sm text-slate-400 mt-1">एडमिन स्टूडियो से खबरें फेच और प्रकाशित करें।</p>
          </div>
        ) : (
          <>
            <div className="flex items-baseline justify-between mb-5 border-b-2 border-[#C8102E]/20 pb-2">
              <h2 className="font-display text-2xl md:text-3xl text-[#121316]">
                {active || "मुख्य समाचार"}
              </h2>
              <span className="text-xs font-mono-j text-slate-500">{articles.length} खबरें</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8" data-testid="news-grid">
              {feature && <NewsCard article={feature} feature index={0} />}
              {rest.map((a, i) => (
                <NewsCard key={a.id} article={a} index={i + 1} />
              ))}
            </div>
          </>
        )}
      </main>

      <footer className="border-t border-[#E4E0D8] mt-12 py-8 text-center text-sm text-slate-500">
        <p className="font-display text-xl text-[#121316]">MyNews</p>
        <p className="mt-1">AI संचालित हिंदी न्यूज़ इंजन · तथ्य सुरक्षा के साथ रीराइट</p>
      </footer>
    </div>
  );
}
