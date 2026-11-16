import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../api";

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
    <div className="auth-grid">
      <div className="auth-side">
        <Link to="/" className="brand mb-12">
          <div className="brand-mark" />
          <span>Code Reviewer</span>
        </Link>

        <h1 className="text-3xl font-extrabold tracking-tighter mb-2">Sign in</h1>
        <p className="text-sm text-ink-soft mb-9">
          Pick up where you left off. Your review history is waiting.
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
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-8 text-xs text-muted">
          No account yet?{" "}
          <Link to="/register" className="text-primary font-medium">
            Create one
          </Link>
        </p>
      </div>

      <div className="auth-visual">
        <div className="demo w-full max-w-md">
          <div className="demo-head">
            <span>session.py — review output</span>
            <span className="demo-score">
              <span className="n" style={{ color: "var(--danger)" }}>60</span>
              <span className="l">score</span>
            </span>
          </div>
          <div className="demo-body">
            <pre className="demo-code">
              <code>
                <span className="flag">query = "SELECT * FROM users WHERE id=" + uid</span>{"\n"}
                <span>cursor.execute(query)</span>
              </code>
            </pre>
            <div className="demo-finding">
              <div className="demo-finding-top">
                <span className="demo-finding-title">SQL built by string concatenation</span>
                <span className="demo-finding-meta">SEC004 · line 1</span>
              </div>
              <p className="demo-finding-body">
                Concatenating user input into SQL allows injection attacks.
              </p>
              <pre className="demo-finding-fix">cursor.execute("SELECT * FROM users WHERE id=?", (uid,))</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
