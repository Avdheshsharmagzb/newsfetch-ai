import { Link } from "react-router-dom";
import { Newspaper, LayoutDashboard } from "lucide-react";

export function PublicHeader({ categories = [], active, onCategory }) {
  const today = new Date().toLocaleDateString("hi-IN", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });

  return (
    <header className="bg-white border-b border-[#E4E0D8] sticky top-0 z-40">
      {/* breaking ticker */}
      <div className="bg-[#C8102E] text-white overflow-hidden">
        <div className="max-w-7xl mx-auto flex items-center">
          <span className="bg-[#121316] text-white text-xs font-mono-j font-bold px-3 py-1.5 shrink-0">
            ताज़ा
          </span>
          <div className="overflow-hidden flex-1">
            <div className="animate-ticker whitespace-nowrap py-1.5 text-sm font-medium">
              दुनिया भर की विदेशी खबरें अब हिंदी में · AI द्वारा रीराइट · तथ्य पूरी तरह सुरक्षित · &nbsp;&nbsp;
              दुनिया भर की विदेशी खबरें अब हिंदी में · AI द्वारा रीराइट · तथ्य पूरी तरह सुरक्षित · &nbsp;&nbsp;
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2" data-testid="logo-home-link">
          <Newspaper className="w-7 h-7 text-[#C8102E]" />
          <div>
            <span className="font-display text-3xl text-[#121316] leading-none">MyNews</span>
            <p className="text-[10px] font-mono-j uppercase tracking-[0.2em] text-slate-500">
              हिंदी समाचार · AI इंजन
            </p>
          </div>
        </Link>
        <div className="hidden md:block text-sm text-slate-600 font-medium">{today}</div>
        <Link
          to="/admin"
          data-testid="admin-nav-link"
          className="flex items-center gap-2 bg-[#121316] hover:bg-black text-white text-sm font-semibold px-4 py-2 rounded-md transition-colors"
        >
          <LayoutDashboard className="w-4 h-4" /> एडमिन स्टूडियो
        </Link>
      </div>

      {categories.length > 0 && (
        <nav className="max-w-7xl mx-auto px-4 sm:px-8 pb-3 flex gap-2 flex-wrap">
          <button
            onClick={() => onCategory(null)}
            data-testid="category-filter-all"
            className={`text-sm font-semibold px-3 py-1.5 rounded-full transition-colors ${
              !active ? "bg-[#C8102E] text-white" : "bg-[#F2EEE7] text-slate-700 hover:bg-[#E4E0D8]"
            }`}
          >
            सभी
          </button>
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => onCategory(c)}
              data-testid={`category-filter-${c}`}
              className={`text-sm font-semibold px-3 py-1.5 rounded-full transition-colors ${
                active === c ? "bg-[#C8102E] text-white" : "bg-[#F2EEE7] text-slate-700 hover:bg-[#E4E0D8]"
              }`}
            >
              {c}
            </button>
          ))}
        </nav>
      )}
    </header>
  );
}
