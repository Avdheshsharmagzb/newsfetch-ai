import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { NewsImage } from "@/components/NewsImage";
import { CATEGORY_META, timeAgo } from "@/lib/newsApi";

export function NewsCard({ article, feature = false, index = 0 }) {
  const meta = CATEGORY_META[article.category] || {};
  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
      className={`group bg-white border border-[#E4E0D8] rounded-lg overflow-hidden hover:shadow-xl hover:shadow-black/5 transition-shadow ${
        feature ? "md:col-span-2 md:row-span-2" : ""
      }`}
      data-testid={`article-card-${article.id}`}
    >
      <Link to={`/article/${article.id}`} className="block h-full">
        <NewsImage
          src={article.image_url}
          alt={article.rewritten_headline}
          watermark={article.watermark_text}
          showFactShield={article.ai_processed}
          className={feature ? "h-64 md:h-80" : "h-44"}
        />
        <div className="p-4 md:p-5">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-mono-j uppercase tracking-[0.15em] font-semibold text-[#C8102E]">
              {meta.emoji} {article.category}
            </span>
            {article.ai_processed && (
              <span className="flex items-center gap-1 text-[10px] font-mono-j text-amber-600">
                <Sparkles className="w-3 h-3" /> AI
              </span>
            )}
          </div>
          <h3
            data-testid="article-card-headline"
            className={`font-display text-[#121316] leading-snug group-hover:text-[#C8102E] transition-colors line-clamp-3 ${
              feature ? "text-2xl md:text-3xl" : "text-lg"
            }`}
          >
            {article.rewritten_headline}
          </h3>
          {feature && (
            <p className="mt-3 text-slate-600 leading-relaxed line-clamp-3">
              {article.rewritten_article}
            </p>
          )}
          <div className="mt-3 flex items-center gap-3 text-xs text-slate-500 font-mono-j">
            <span>{timeAgo(article.published_at || article.created_at)}</span>
            {article.source_name && <span>· स्रोत: {article.source_name}</span>}
          </div>
        </div>
      </Link>
    </motion.article>
  );
}
