import { useState } from "react";
import { Link } from "react-router-dom";
import { register } from "../api";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await register({ email, password });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.detail || "Registration failed");
        return;
      }
      const loginRes = await fetch(
        `${import.meta.env.VITE_API_BASE || "http://localhost:8000"}/api/auth/login`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        }
      );
      if (!loginRes.ok) {
        setError("Account created, but login failed. Try signing in.");
        return;
      }
      const ld = await loginRes.json();
      localStorage.setItem("token", ld.access_token);
      window.location.href = "/";
    } catch {
      setError("Network error. Is the backend running on localhost:8000?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-56px)] flex items-center justify-center px-4">
      <div className="max-w-sm w-full">
        <div className="flex items-center gap-3 mb-8">
          <div className="brand-mark" />
          <h1 className="text-xl font-extrabold tracking-tighter">Code Reviewer</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-wider">Email address</label>
            <input
              type="email"
              required
              className="input w-full"
              placeholder="you@college.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-wider">Password</label>
            <input
              type="password"
              required
              minLength={8}
              className="input w-full"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && (
            <div className="rounded bg-red-50 border border-red-100 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn w-full btn-primary">
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-8 text-center text-[11px] text-slate-400">
          Already have an account?{" "}
          <Link to="/login" className="text-accent font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
