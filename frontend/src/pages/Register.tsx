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
      window.location.href = "/submit";
    } catch {
      setError("Network error. Is the backend running on localhost:8000?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-grid">
      <div className="auth-side">
        <Link to="/" className="brand mb-12">
          <div className="brand-mark" />
          <span>Code Reviewer</span>
        </Link>

        <h1 className="text-3xl font-extrabold tracking-tighter mb-2">Create account</h1>
        <p className="text-sm text-ink-soft mb-9">
          Free, takes ten seconds, and every review gets saved to your history.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="field-label">Email address</label>
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
            <label className="field-label">Password</label>
            <input
              type="password"
              required
              minLength={8}
              className="input w-full"
              placeholder="At least 8 characters"
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

        <p className="mt-8 text-xs text-muted">
          Already registered?{" "}
          <Link to="/login" className="text-primary font-medium">
            Sign in
          </Link>
        </p>
      </div>

      <div className="auth-visual">
        <div className="demo w-full max-w-md">
          <div className="demo-head">
            <span>config.py — review output</span>
            <span className="demo-score">
              <span className="n" style={{ color: "var(--warn)" }}>90</span>
              <span className="l">score</span>
            </span>
          </div>
          <div className="demo-body">
            <pre className="demo-code">
              <code>
                <span>api_key = "sk-live-9f3a2b8c"</span>{"\n"}
                <span>requests.get(url, verify=False)</span>
              </code>
            </pre>
            <div className="demo-finding" style={{ borderLeftColor: "var(--warn)" }}>
              <div className="demo-finding-top">
                <span className="demo-finding-title">Hardcoded credential</span>
                <span className="demo-finding-meta">SEC003 · line 1</span>
              </div>
              <p className="demo-finding-body">
                Secrets committed in source leak through version history and
                shared repos.
              </p>
              <pre className="demo-finding-fix">api_key = os.environ["API_KEY"]</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
