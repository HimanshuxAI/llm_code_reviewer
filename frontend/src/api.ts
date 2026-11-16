const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export function token(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request(path: string, opts: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
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
