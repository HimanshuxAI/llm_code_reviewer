import { Link, useNavigate } from "react-router-dom";
import { FileCode2, Folder, ShieldCheck, History as HistoryIcon, Plus } from "lucide-react";

const RULES = [
  { id: "SEC001", desc: "eval() executes untrusted input as code", sev: "critical" },
  { id: "SEC003", desc: "Credentials hardcoded in source", sev: "high" },
  { id: "SEC004", desc: "SQL query built by string concatenation", sev: "high" },
  { id: "SEC006", desc: "TLS certificate verification disabled", sev: "high" },
  { id: "SEC009", desc: "Unsafe C string functions (gets, strcpy)", sev: "high" },
  { id: "SEC010", desc: "OS command execution with interpolated input", sev: "high" },
  { id: "SEC005", desc: "Broken hash algorithm (MD5, SHA1)", sev: "medium" },
  { id: "SEC008", desc: "Unsanitized innerHTML assignment (XSS)", sev: "medium" },
  { id: "SEC012", desc: "Predictable random used for tokens", sev: "medium" },
  { id: "QUAL001", desc: "Bare except clause hides real errors", sev: "low" },
];

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
            <a href="#how" className="nav-link">How it works</a>
            <a href="#rules" className="nav-link">Rules</a>
            {token ? (
              <button
                onClick={() => {
                  localStorage.removeItem("token");
                  navigate("/login");
                }}
                className="btn btn-ghost"
              >
                Sign out
              </button>
            ) : (
              <>
                <Link to="/login" className="btn btn-ghost">Sign in</Link>
                <Link to="/register" className="btn btn-primary">Create account</Link>
              </>
            )}
          </div>
        </div>
      </div>

      <main>
        <section className="page paper-lines">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="eyebrow mb-6">Built-in analysis engine</p>
              <h1 className="display mb-7">
                Find the bug before
                <br />
                your professor does.
              </h1>
              <p className="lede mb-9">
                Paste your code. Get every bug, vulnerability, and bad practice
                found — each explained in plain English with a fix you can
                apply, and a quality score from 0 to 100.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Link to="/submit" className="btn btn-primary px-7 py-3">
                  Review my code
                </Link>
                <Link to="/register" className="btn btn-ghost px-7 py-3">
                  Create free account
                </Link>
              </div>
            </div>

            <div className="demo">
              <div className="demo-head">
                <span>workspace — code review</span>
                <span className="demo-score">
                  <span className="n">80</span>
                  <span className="l">score</span>
                </span>
              </div>
              <div className="demo-body" style={{ padding: 0 }}>
                <div style={{ display: "grid", gridTemplateColumns: "40px 150px 1fr 200px", minHeight: "330px" }}>
                  <div
                    className="rail"
                    style={{ gridRow: "1 / -1", position: "relative" }}
                  >
                    <div className="rail-logo" style={{ width: 22, height: 22 }} />
                    <div className="rail-item active" style={{ width: 30, height: 30 }}>
                      <Plus className="h-4 w-4" />
                    </div>
                    <div className="rail-item" style={{ width: 30, height: 30 }}>
                      <HistoryIcon className="h-4 w-4" />
                    </div>
                  </div>

                  <div className="tree" style={{ gridRow: "1 / 2", padding: "10px 0" }}>
                    <div className="tree-head">Explorer</div>
                    <div className="tree-folder">
                      <Folder className="h-3.5 w-3.5" /> project
                    </div>
                    <div className="tree-item active">login.py</div>
                    <div className="tree-item">db.py</div>
                    <div className="tree-item">utils.py</div>
                  </div>

                  <div className="ide-main" style={{ gridRow: "1 / 2" }}>
                    <div className="ide-tabs">
                      <div className="ide-tab active">
                        <FileCode2 className="h-3 w-3" /> login.py
                      </div>
                    </div>
                    <div className="ide-editor">
                      <div className="ide-gutter">
                        <div className="ide-gutter-line">1</div>
                        <div className="ide-gutter-line flagged">2</div>
                        <div className="ide-gutter-line flagged">3</div>
                        <div className="ide-gutter-line">4</div>
                        <div className="ide-gutter-line">5</div>
                        <div className="ide-gutter-line">6</div>
                      </div>
                      <div className="ide-code">
                        <span className="tok-key">import</span> os{"\n"}
                        <span className="tok-key">password</span> = <span className="tok-str">"hunter2hunter2"</span>{"\n"}
                        <span className="tok-flag">os.system(<span className="tok-str">"ls "</span> + input())</span>{"\n"}
                        {"\n"}
                        <span className="tok-key">def</span> <span className="tok-fn">login</span>(user, pwd):{"\n"}
                        {"    "}<span className="tok-key">return</span> <span className="tok-key">True</span>
                      </div>
                    </div>
                  </div>

                  <div className="inspector" style={{ gridRow: "1 / 2" }}>
                    <div className="inspector-head">
                      <span className="inspector-title">Problems</span>
                      <span className="tree-badge crit">2</span>
                    </div>
                    <div className="inspector-body">
                      <div className="issue sev-high">
                        <div className="issue-top">
                          <span className="issue-title">Hardcoded credential</span>
                        </div>
                        <div className="issue-meta">SEC003 · line 2</div>
                        <p className="issue-text">
                          Secrets committed in source leak through history.
                        </p>
                      </div>
                      <div className="issue sev-high">
                        <div className="issue-top">
                          <span className="issue-title">OS command execution</span>
                        </div>
                        <div className="issue-meta">SEC010 · line 3</div>
                        <p className="issue-text">
                          os.system interpolates input straight into a shell.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="statusbar" style={{ gridColumn: "1 / -1", position: "relative" }}>
                  <div className="status-left">
                    <span className="status-item">
                      <ShieldCheck className="h-3 w-3" /> code-reviewer
                    </span>
                    <span>python</span>
                  </div>
                  <div className="status-right">
                    <span>2 problems</span>
                    <span className="status-score">score 80/100</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="how" className="page" style={{ paddingTop: 0 }}>
          <p className="eyebrow mb-8">Pipeline</p>
          <div>
            <div className="step-row">
              <div className="step-num">01</div>
              <div>
                <h3 className="step-title">Language detection</h3>
                <p className="step-body">
                  Filename and content heuristics identify Python, JavaScript,
                  Java, C, or C++ so the right rules and reviewer run against
                  your code.
                </p>
              </div>
            </div>
            <div className="step-row">
              <div className="step-num">02</div>
              <div>
                <h3 className="step-title">Regex security rules</h3>
                <p className="step-body">
                  Fourteen pattern rules run over every line — hardcoded
                  secrets, SQL injection, unsafe eval, weak crypto, buffer
                  risks. Comments are masked first, so commented-out code is
                  not flagged.
                </p>
              </div>
            </div>
            <div className="step-row">
              <div className="step-num">03</div>
              <div>
                <h3 className="step-title">Built-in analysis engine</h3>
                <p className="step-body">
                  Six local analysis passes run over your code: dataflow
                  tracking, secret detection by entropy, Python AST checks,
                  per-language dangerous patterns, and quality metrics.
                  Nothing leaves your machine.
                </p>
              </div>
            </div>
            <div className="step-row">
              <div className="step-num">04</div>
              <div>
                <h3 className="step-title">Merge and score</h3>
                <p className="step-body">
                  Duplicate findings collapse into one. Each severity carries a
                  weight — critical costs 20 points, low costs 2 — and the
                  result is your score.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="rules" className="page" style={{ paddingTop: 0 }}>
          <p className="eyebrow mb-6">Rule catalogue</p>
          <h2 className="section-title mb-2">What the scanner looks for</h2>
          <p className="lede mb-10" style={{ fontSize: 16 }}>
            Every rule ships with the project. These are the ones the static
            scanner checks today.
          </p>
          <div className="rule-table">
            {RULES.map((r) => (
              <div key={r.id} className="rule-row">
                <span className="rule-id">{r.id}</span>
                <span className="rule-desc">{r.desc}</span>
                <span className={`rule-sev ${r.sev}`}>{r.sev}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="page" style={{ paddingTop: 0 }}>
          <div className="panel p-12 text-center">
            <p className="eyebrow mb-5" style={{ justifyContent: "center" }}>
              Start now
            </p>
            <h2 className="display mb-5" style={{ fontSize: "clamp(28px, 4vw, 40px)" }}>
              Your next commit deserves a second pair of eyes.
            </h2>
            <p className="lede mb-8" style={{ margin: "0 auto 32px" }}>
              Free to use. No card needed. Bring your code, get a review in
              seconds.
            </p>
            <Link to="/submit" className="btn btn-primary px-8 py-3">
              Review my code
            </Link>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="page py-8 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-ink-soft">
            <div className="brand-mark" style={{ width: 16, height: 16 }} />
            <span>LLM-Powered Secure Code Review Assistant</span>
          </div>
          <div className="flex gap-6 text-sm">
            <Link to="/login" className="text-ink-soft hover:text-primary">Sign in</Link>
            <Link to="/register" className="text-ink-soft hover:text-primary">Create account</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
