import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getReview } from "../api";
import { type ReviewDetail } from "../api";
import ScoreGauge from "../components/ScoreGauge";
import FindingCard from "../components/FindingCard";
import { RefreshCw, AlertCircle } from "lucide-react";

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
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
          <p className="text-sm text-gray-600">Loading review…</p>
        </div>
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-10 w-10 text-red-500 mx-auto mb-3" />
          <h2 className="text-lg font-medium text-gray-900">{error || "Review not found"}</h2>
          <button
            onClick={() => navigate("/submit")}
            className="mt-4 btn btn-outline"
          >
            Submit new code
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Review results</h1>
          <p className="mt-1 text-sm text-gray-600">
            Language: <span className="font-mono text-gray-900">{review.language}</span>
          </p>
        </div>
        <Link to="/history" className="btn-outline px-3 py-1.5 text-sm font-medium">
          Back to history
        </Link>
      </div>

      <ScoreGauge score={review.score} />

      <div className="flex gap-2 mb-6">
        {[
          { key: "critical", label: "Critical", cls: "border-red-200 bg-red-50 text-red-700" },
          { key: "high", label: "High", cls: "border-orange-200 bg-orange-50 text-orange-700" },
          { key: "medium", label: "Medium", cls: "border-amber-200 bg-amber-50 text-amber-700" },
          { key: "low", label: "Low", cls: "border-gray-200 bg-gray-50 text-gray-700" },
        ].map((sev) => (
          <span
            key={sev.key}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold border ${
              counts[sev.key] > 0 ? sev.cls : "border-transparent bg-gray-100 text-gray-400"
            }`}
          >
            {sev.label}: {counts[sev.key]}
          </span>
        ))}
      </div>

      {review.findings.length === 0 ? (
        <div className="panel p-8 text-center shadow-sm">
          <span className="text-green-600 text-2xl">✓</span>
          <h2 className="mt-3 text-lg font-medium text-gray-900">No issues found</h2>
          <p className="mt-1 text-sm text-gray-600">
            Your code looks clean on both static scan and AI review.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {review.findings.map((f) => (
            <FindingCard key={`${f.rule_id}-${f.line}`} finding={f} />
          ))}
        </div>
      )}

      <div className="pt-4 border-t border-gray-200 flex items-center justify-between text-sm text-gray-500">
        <span>
          Reviewed {new Date(review.created_at).toLocaleString()}
        </span>
      </div>
    </div>
  );
}
