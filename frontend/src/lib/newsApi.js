import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

export const CATEGORY_META = {
  "दुनिया": { emoji: "🌍", en: "World" },
  "व्यापार": { emoji: "📈", en: "Business" },
  "तकनीक": { emoji: "💡", en: "Tech" },
  "खेल": { emoji: "⚽", en: "Sports" },
  "मनोरंजन": { emoji: "🎬", en: "Entertainment" },
  "राजनीति": { emoji: "🏛️", en: "Politics" },
};

export function timeAgo(iso) {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "अभी";
  if (diff < 3600) return `${Math.floor(diff / 60)} मिनट पहले`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} घंटे पहले`;
  return `${Math.floor(diff / 86400)} दिन पहले`;
}
