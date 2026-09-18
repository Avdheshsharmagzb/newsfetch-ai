import { ShieldCheck } from "lucide-react";

// Displays a news image with a persistent "MyNews" brand watermark overlay.
export function NewsImage({ src, alt, watermark = "MyNews", className = "", showFactShield = false }) {
  return (
    <div className={`relative overflow-hidden bg-[#E4E0D8] ${className}`}>
      {src ? (
        <img
          src={src}
          alt={alt}
          data-testid="news-image"
          className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-[#C8102E] font-display text-2xl">
          MyNews
        </div>
      )}
      {/* watermark badge (always visible branding) */}
      <div
        data-testid="image-watermark"
        className="absolute bottom-2 right-2 bg-[#C8102E]/90 text-white text-xs font-mono-j font-semibold px-2 py-0.5 rounded-sm backdrop-blur-sm shadow"
      >
        {watermark}
      </div>
      {showFactShield && (
        <div className="absolute top-2 left-2 flex items-center gap-1 bg-emerald-600/90 text-white text-[10px] font-mono-j px-2 py-0.5 rounded-sm">
          <ShieldCheck className="w-3 h-3" /> तथ्य सुरक्षित
        </div>
      )}
    </div>
  );
}
