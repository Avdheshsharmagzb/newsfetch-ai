import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Newspaper, Lock, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

function formatErr(detail) {
  if (!detail) return "कुछ गड़बड़ हुई। दोबारा कोशिश करें।";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e?.msg || "").join(" ");
  return String(detail);
}

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email.trim(), password);
      navigate("/admin");
    } catch (err) {
      setError(formatErr(err?.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F1117] text-slate-100 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-[#181B24] border border-[#2B303E] rounded-2xl p-8"
      >
        <div className="flex items-center gap-2 mb-1">
          <Newspaper className="w-7 h-7 text-[#C8102E]" />
          <span className="font-display text-3xl">MyNews</span>
        </div>
        <p className="text-sm text-slate-400 mb-6 font-mono-j uppercase tracking-[0.15em]">एडमिन स्टूडियो लॉगिन</p>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-xs font-mono-j text-slate-400 uppercase tracking-wider">ईमेल</label>
            <input
              data-testid="login-email-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@mynews.com"
              required
              className="mt-1 w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2.5 text-slate-100 focus:border-[#C8102E] outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-mono-j text-slate-400 uppercase tracking-wider">पासवर्ड</label>
            <input
              data-testid="login-password-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="mt-1 w-full bg-[#0F1117] border border-[#2B303E] rounded-md px-3 py-2.5 text-slate-100 focus:border-[#C8102E] outline-none"
            />
          </div>

          {error && (
            <div data-testid="login-error" className="text-sm text-rose-400 bg-rose-950/30 border border-rose-900 rounded-md px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            data-testid="login-submit-btn"
            className="w-full flex items-center justify-center gap-2 bg-[#C8102E] hover:bg-[#A00C23] disabled:opacity-60 text-white font-semibold py-2.5 rounded-md transition-colors"
          >
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
            लॉगिन करें
          </button>
        </form>

        <Link to="/" className="block text-center text-sm text-slate-500 hover:text-white mt-5" data-testid="login-back-site">
          ← न्यूज़ साइट पर लौटें
        </Link>
      </motion.div>
    </div>
  );
}
