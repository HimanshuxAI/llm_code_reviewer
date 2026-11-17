import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getReview } from "../api";
import { type ReviewDetail } from "../api";
import Workspace from "../components/Workspace";
import EmptyState from "../components/EmptyState";
import { FileCode2, Check } from "lucide-react";

export default function Results() {
  const { id } = useParams();
  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getReview(Number(id))
      .then(async (res) => {
        if (!res.ok) {
          setError("Review not found");
          return;
        }
        setReview(await res.json());
      })
      .catch(() => setError("Network error loading review"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="loader">
          <div className="loader-dot" />
          <p className="loader-text">Analyzing code...</p>
        </div>
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="page">
        <EmptyState
          title="Review not found"
          subtitle={error || "The review you are looking for does not exist."}
          action={
            <Link to="/submit" className="btn btn-primary">
              Submit new code
            </Link>
          }
        />
      </div>
    );
  }

  const source = review.source_code ?? "";
  const lines = source.split("\n");
  const flagged = new Set(review.findings.map((f) => f.line));
  const criticalCount = review.findings.filter((f) => f.severity === "critical").length;
  const warnCount = review.findings.filter(
    (f) => f.severity === "high" || f.severity === "medium"
  ).length;

  return (
    <Workspace
      tab={`review-${review.id}.py`}
      status={{
        left: `${lines.length} lines · ${review.language}`,
        right: `${review.findings.length} problems`,
        score: review.score,
      }}
      tree={
        <>
          <div className="tree-head">Review #{review.id}</div>
          <div className="tree-folder">
            <FileCode2 className="h-3.5 w-3.5" /> submitted
          </div>
          <div className="tree-item active">source.{review.language === "python" ? "py" : review.language.slice(0, 2)}</div>
          <div style={{ padding: "14px 14px 0" }}>
            {criticalCount > 0 && (
              <div className="tree-badge crit" style={{ display: "inline-block", marginBottom: 6 }}>
                {criticalCount} critical
              </div>
            )}
            {warnCount > 0 && (
              <div className="tree-badge warn" style={{ display: "inline-block" }}>
                {warnCount} warnings
              </div>
            )}
            {criticalCount === 0 && warnCount === 0 && (
              <div className="tree-badge ok" style={{ display: "inline-block" }}>
                clean
              </div>
            )}
          </div>
        </>
      }
      inspector={
        <>
          <div className="inspector-head">
            <span className="inspector-title">Problems</span>
            <span className={`tree-badge ${criticalCount > 0 ? "crit" : warnCount > 0 ? "warn" : "ok"}`}>
              {review.findings.length}
            </span>
          </div>
          <div className="inspector-body">
            {review.findings.length === 0 ? (
              <div className="flex flex-col items-center py-8 text-center">
                <Check className="h-8 w-8 text-success mb-3" />
                <p className="text-sm font-bold text-ink">No issues found</p>
                <p className="text-xs text-muted mt-1">
                  Every analysis pass came back clean.
                </p>
              </div>
            ) : (
              review.findings.map((f) => (
                <div key={`${f.rule_id}-${f.line}`} className={`issue sev-${f.severity}`}>
                  <div className="issue-top">
                    <span className="issue-title">{f.title}</span>
                  </div>
                  <div className="issue-meta">
                    {f.rule_id} · line {f.line} · {f.source}
                    {f.confidence === "medium" && (
                      <span style={{ color: "var(--warn)" }}>
                        {" "}· inferred (medium confidence)
                      </span>
                    )}
                  </div>
                  <p className="issue-text">{f.explanation}</p>
                  {f.evidence && (
                    <pre
                      className="issue-fix"
                      style={{
                        background: "var(--card)",
                        borderColor: "var(--rule)",
                        color: "var(--ink-soft)",
                      }}
                    >
                      {f.evidence}
                    </pre>
                  )}
                  {f.fixed_snippet && <pre className="issue-fix">{f.fixed_snippet}</pre>}
                </div>
              ))
            )}
          </div>
        </>
      }
    >
      <div className="ide-editor">
        <div className="ide-gutter">
          {lines.map((_, i) => (
            <div
              key={i}
              className={`ide-gutter-line ${flagged.has(i + 1) ? "flagged" : ""}`}
            >
              {i + 1}
            </div>
          ))}
        </div>
        <div className="ide-code">
          <pre>
            {lines.map((line, i) => (
              <span key={i} className={flagged.has(i + 1) ? "tok-flag" : undefined}>
                {line}
                {"\n"}
              </span>
            ))}
          </pre>
        </div>
      </div>
    </Workspace>
  );
}
