import { useState } from "react";
import { Link } from "react-router-dom";
import { register } from "../api";
import { Mail, Lock, User } from "lucide-react";

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
    <div className="flex min-h-screen items-center justify-center bg-black/50 px-4">
      <div className="max-w-md w-full glass p-8 shadow-2xl">
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <User className="h-5 w-5 text-blue-400" />
            <h1 className="text-xl font-bold text-white">Create account</h1>
          </div>
          <p className="text-sm text-slate-400">Join to save your review history on your dashboard.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Email address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
              <input
                type="email"
                required
                className="input pl-10"
                placeholder="you@college.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
              <input
                type="password"
                required
                minLength={8}
                className="input pl-10"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn w-full btn-primary">
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-8 text-center text-xs text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-400 hover:underline ml-1">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
