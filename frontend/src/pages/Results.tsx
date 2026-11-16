import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getReview } from "../api";
import { type ReviewDetail } from "../api";
import ScoreDonut from "../components/ScoreDonut";
import FindingCard from "../components/FindingCard";
import DiffPreview from "../components/DiffPreview";
import CopyButton from "../components/CopyButton";
import { AlertCircle } from "lucide-react";
import ScanLoader from "../components/ScanLoader";

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
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
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4">
        <ScanLoader />
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4">
        <div className="max-w-md">
          <EmptyStatePage
            title="Review not found"
            subtitle={error || "The review you&apos;re looking for doesn&apos;t exist."}
            action={
              <button
                onClick={() => navigate("/submit")}
                className="btn btn-primary"
              >
                Submit new code
              </button>
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="h1">Review results</h1>
          <p className="mt-2 text-sm text-slate-500">
            Language: <span className="font-mono text-slate-700">{review.language}</span>
          </p>
        </div>
        <Link to="/history" className="btn btn-outline px-3 py-1.5 text-xs font-bold">
          Back to history
        </Link>
      </div>

      <ScoreDonut score={review.score} />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          { key: "critical", label: "Critical", color: "text-red-600", border: "border-red-500/20", bg: "bg-red-50" },
          { key: "high", label: "High", color: "text-orange-600", border: "border-orange-500/20", bg: "bg-orange-50" },
          { key: "medium", label: "Medium", color: "text-amber-600", border: "border-amber-500/20", bg: "bg-amber-50" },
          { key: "low", label: "Low", color: "text-emerald-600", border: "border-emerald-500/20", bg: "bg-emerald-50" },
        ].map((sev) => (
          <span
            key={sev.key}
            className={`px-3 py-2 rounded-xl text-xs font-bold border ${counts[sev.key] > 0 ? sev.color + " " + sev.border + " " + sev.bg : "border-transparent bg-white text-slate-400"}`}
          >
            {sev.label}: {counts[sev.key]}
          </span>
        ))}
      </div>

      <div className="grid gap-4">
        {review.findings.length === 0 ? (
          <div className="panel p-12 text-center border-dashed border-blue-100 shadow-sm">
            <span className="text-emerald-500 text-3xl mb-3">✓</span>
            <h2 className="text-lg font-bold text-slate-800 mb-1">No issues found</h2>
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

      <DiffPreview source_code={review.source_code} fixed_snippet={review.findings.find((f) => f.fixed_snippet)?.fixed_snippet ?? null} />

      <div className="pt-5 border-t border-white/80 flex items-center justify-between text-xs text-slate-400">
        <span>
          Reviewed <span className="text-slate-700 font-medium">{new Date(review.created_at).toLocaleString()}</span>
        </span>
        <CopyButton text={review.source_code} />
      </div>
    </div>
  );
}

function EmptyStatePage({ title, subtitle, action }: { title: string; subtitle: string; action: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-20 h-20 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-7 text-blue-500">
        <AlertCircle className="h-9 w-9" />
      </div>
      <h2 className="text-lg font-bold text-slate-800">{title}</h2>
      <p className="mt-3 text-sm text-slate-500 max-w-xs">{subtitle}</p>
      <div className="mt-9">{action}</div>
    </div>
  );
}
