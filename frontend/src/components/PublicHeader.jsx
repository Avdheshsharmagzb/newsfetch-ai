import { Link } from "react-router-dom";
import { SITE_NAME, NUM_PAGES } from "@/lib/newsApi";

export function PublicHeader({ activePage = 1, onPage }) {
  const today = new Date().toLocaleDateString("hi-IN", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
  const pages = Array.from({ length: NUM_PAGES }, (_, i) => i + 1);

  return (
    <header className="bg-white border-b-2 border-[#121316] sticky top-0 z-40">
      {/* breaking ticker */}
      <div className="bg-[#C8102E] text-white overflow-hidden">
        <div className="max-w-7xl mx-auto flex items-center">
          <span className="bg-[#121316] text-white text-xs font-mono-j font-bold px-3 py-1.5 shrink-0">
            ताज़ा
          </span>
          <div className="overflow-hidden flex-1">
            <div className="animate-ticker whitespace-nowrap py-1.5 text-sm font-medium">
              दुनिया भर की खबरें अब हिंदी में · तथ्य पूरी तरह सुरक्षित · विश्वसनीय समाचार · &nbsp;&nbsp;
              दुनिया भर की खबरें अब हिंदी में · तथ्य पूरी तरह सुरक्षित · विश्वसनीय समाचार · &nbsp;&nbsp;
            </div>
          </div>
        </div>
      </div>

      {/* masthead */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-5 flex flex-col items-center text-center">
        <Link to="/" data-testid="logo-home-link" className="leading-none">
          <h1 className="font-rozha text-5xl sm:text-6xl text-[#121316] tracking-tight">{SITE_NAME}</h1>
          <p className="mt-1 text-xs font-mono-j uppercase tracking-[0.35em] text-[#C8102E]">
            विश्वसनीय हिंदी समाचार
          </p>
        </Link>
        <div className="mt-2 text-xs text-slate-500 font-medium border-t border-[#E4E0D8] pt-2 w-full max-w-md">
          {today}
        </div>
      </div>

      {/* page navigation (newspaper pages) */}
      <nav className="border-t border-[#121316] bg-[#FAF7F2]">
        <div className="max-w-7xl mx-auto px-4 sm:px-8 flex justify-center gap-1 sm:gap-2 flex-wrap">
          {pages.map((p) => (
            <button
              key={p}
              onClick={() => onPage(p)}
              data-testid={`page-nav-${p}`}
              className={`text-sm font-semibold px-4 sm:px-6 py-2.5 transition-colors border-b-2 ${
                activePage === p
                  ? "border-[#C8102E] text-[#C8102E]"
                  : "border-transparent text-slate-700 hover:text-[#C8102E]"
              }`}
            >
              पेज {p}
            </button>
          ))}
        </div>
      </nav>
    </header>
  );
}
