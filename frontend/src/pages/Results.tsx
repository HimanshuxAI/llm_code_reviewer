import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getReview } from "../api";
import { type ReviewDetail } from "../api";
import ScoreDial from "../components/ScoreDial";
import FindingCard from "../components/FindingCard";
import DiffPreview from "../components/DiffPreview";
import CopyButton from "../components/CopyButton";
import ScanLoader from "../components/ScanLoader";
import EmptyState from "../components/EmptyState";

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
          setLoading(false);
          return;
        }
        setReview(await res.json());
      })
      .catch(() => {
        setError("Network error loading review");
        setLoading(false);
      })
      .finally(() => setLoading(false));
  }, [id]);

  const counts: Record<string, number> = review
    ? {
        critical: review.findings.filter((f) => f.severity === "critical").length,
        high: review.findings.filter((f) => f.severity === "high").length,
        medium: review.findings.filter((f) => f.severity === "medium").length,
        low: review.findings.filter((f) => f.severity === "low").length,
      }
    : { critical: 0, high: 0, medium: 0, low: 0 };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-56px)] flex items-center justify-center">
        <ScanLoader />
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="page">
        <EmptyState
          title="Review not found"
          subtitle={error || "The review you&apos;re looking for doesn&apos;t exist."}
          action={
            <Link to="/submit" className="btn btn-primary">
              Submit new code
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="page fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="section-title">Review results</h2>
          <p className="section-sub">
            Language:{" "}
            <span className="font-mono text-slate-600">{review.language}</span>
          </p>
        </div>
        <Link to="/history" className="btn btn-ghost text-xs px-2 py-1">
          Back to history
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-3">
          <ScoreDial score={review.score} />

          <div className="mt-6 severity-counts">
            {[
              { key: "critical", label: "Critical", cls: "badge-danger" },
              { key: "high", label: "High", cls: "badge-warn" },
              { key: "medium", label: "Medium", cls: "badge-warn" },
              { key: "low", label: "Low", cls: "badge-success" },
            ].map((sev) => (
              <span
                key={sev.key}
                className={`count-badge ${counts[sev.key] > 0 ? sev.cls : "text-slate-400 border-transparent bg-transparent"}`}
              >
                {sev.label}: <span className="num">{counts[sev.key]}</span>
              </span>
            ))}
          </div>
        </div>

        <div className="lg:col-span-9">
          <div className="grid gap-4">
            {review.findings.length === 0 ? (
              <div className="panel p-8 text-center border-dashed border-line">
                <span className="text-success text-2xl mb-3">✓</span>
                <h3 className="text-lg font-bold text-ink mb-1">No issues found</h3>
                <p className="text-sm text-slate-500">
                  Your code looks clean on both static scan and AI review.
                </p>
              </div>
            ) : (
              review.findings.map((f) => (
                <FindingCard key={`${f.rule_id}-${f.line}`} finding={f} />
              ))
            )}
          </div>

          <DiffPreview
            source_code={review.source_code}
            fixed_snippet={
              review.findings.find((f) => f.fixed_snippet)?.fixed_snippet ?? null
            }
          />
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-line flex items-center justify-between text-[11px] text-slate-400">
        <span>
          Reviewed{" "}
          <span className="text-ink font-medium">{new Date(review.created_at).toLocaleString()}</span>
        </span>
        <CopyButton text={review.source_code} />
      </div>
    </div>
  );
}


