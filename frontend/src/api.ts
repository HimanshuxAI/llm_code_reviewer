// API base. Unset means same origin (works when the SPA is served from the
// same host as the API, e.g. the Render single-container deploy). For local
// dev with Vite on :5173 and the API on :8000, set VITE_API_BASE in .env.
const API_BASE = import.meta.env.VITE_API_BASE || "";

// Namespaced on purpose. localhost:5173 is shared with any other app on
// that port, and a generic "token" key let one app's session overwrite
// another's — the other app's token then reached this API and came back
// 401 on a perfectly good review.
const TOKEN_KEY = "code-reviewer.token";

export function token(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(value: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, value);
}

export function clearToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

function handleUnauthorized(res: Response, path: string) {
  if (res.status !== 401) return;
  if (path.startsWith("/api/auth/")) return;
  clearToken();
  if (typeof window === "undefined") return;
  if (window.location.pathname.startsWith("/login")) return;
  window.location.assign("/login?expired=1");
}

async function request(path: string, opts: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  handleUnauthorized(res, path);
  return res;
}

export interface AuthPayload {
  email: string;
  password: string;
}

export interface ReviewCreate {
  source_code: string;
  filename?: string;
}

export interface Finding {
  rule_id: string;
  title: string;
  severity: string;
  line: number;
  explanation: string;
  suggestion: string;
  source: string;
  fixed_snippet: string | null;
  evidence?: string;
  confidence?: "high" | "medium";
  related_lines?: number[];
}

export interface ReviewSummary {
  id: number;
  language: string;
  score: number;
  created_at: string;
}

export interface ReviewDetail extends ReviewSummary {
  source_code: string;
  findings: Finding[];
}

export async function register(data: AuthPayload) {
  return request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function login(data: AuthPayload) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function submitReview(data: ReviewCreate) {
  return request("/api/reviews", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listReviews() {
  return request("/api/reviews");
}

export async function getReview(id: number) {
  return request(`/api/reviews/${id}`);
}
