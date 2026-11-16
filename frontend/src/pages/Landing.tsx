import { Link, useNavigate } from "react-router-dom";
import { Code2, ShieldCheck, Zap, Clock } from "lucide-react";

export default function Landing() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  return (
    <div className="shell">
      <div className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            <div className="brand-mark" />
            <span>Code Reviewer</span>
          </Link>

          <div className="nav-links">
            {token ? (
              <>
                <Link to="/history" className="nav-link">
                  <Clock className="h-4 w-4 mr-1" /> History
                </Link>
                <button
                  onClick={() => {
                    localStorage.removeItem("token");
                    navigate("/login");
                  }}
                  className="btn btn-ghost"
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-ghost">Sign in</Link>
                <Link to="/register" className="btn btn-primary">Create account</Link>
              </>
            )}
          </div>
        </div>
      </div>

      <main className="page">
        <section className="flex flex-col lg:flex-row gap-12 items-center">
          <div className="lg:w-1/2">
            <h1 className="text-5xl font-extrabold tracking-tighter leading-[1.1] mb-6">
              Secure code review,<br />
              explained for students.
            </h1>
            <p className="text-lg text-ink-soft mb-8 max-w-lg leading-relaxed">
              Paste or upload your source code and get an instant review — bugs,
              security issues, and quality problems found, explained in plain
              English, with a severity-weighted score from 0 to 100.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/submit" className="btn w-full sm:w-auto btn-primary">
                Start reviewing
              </Link>
              <Link
                to="/register"
                className="btn w-full sm:w-auto btn-ghost"
              >
                Create account
              </Link>
            </div>
          </div>

          <div className="lg:w-1/2 panel p-8 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 -mx-8 -mt-8 w-64 h-64 bg-accent/10 rounded-full blur-3xl" />
            <div className="flex flex-col gap-5">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-ink">Security first</h3>
                  <p className="text-sm text-ink-soft">
                    Heuristic scan catches hardcoded secrets, SQL injection,
                    unsafe eval, and more — always on, no API key needed.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center text-accent">
                  <Zap className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-ink">AI explained</h3>
                  <p className="text-sm text-ink-soft">
                    LLM review adds plain-English explanations and corrected
                    snippets so you actually learn from every finding.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center text-success">
                  <Code2 className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-ink">Scored 0-100</h3>
                  <p className="text-sm text-ink-soft">
                    Severity-weighted quality score shows where your code stands
                    and what to fix first.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-16">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-extrabold text-ink mb-4">Ready to review?</h2>
            <p className="text-ink-soft max-w-2xl mx-auto">
              Join other students catching bugs before they become problems.
            </p>
          </div>
          <div className="flex justify-center">
            <Link to="/submit" className="btn btn-primary px-10 py-3">
              Submit your first code
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
