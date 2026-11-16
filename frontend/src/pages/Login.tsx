import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api";
import { Mail, Lock, ShieldCheck } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login({ email, password });
      if (!res.ok) {
        setError(res.status === 401 ? "Invalid email or password" : "Login failed");
        return;
      }
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      navigate("/", { replace: true });
    } catch {
      setError("Network error. Is the backend running on localhost:8000?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="max-w-md w-full glass p-8 shadow-lg">
        <div className="mb-7">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="h-5 w-5 text-blue-500" />
            <h1 className="h2">Sign in</h1>
          </div>
          <p className="text-sm text-slate-500">Review your code securely. Enter your account below.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Email address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
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
            <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
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
            <div className="rounded-xl bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn w-full btn-primary"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-9 text-center text-xs text-slate-500">
          Don't have an account?{" "}
          <a href="/register" className="text-blue-600 hover:text-blue-700 ml-1 font-medium">Create one</a>
        </p>
      </div>
    </div>
  );
}
