import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listReviews } from "../api";
import { type ReviewSummary } from "../api";

import EmptyState from "../components/EmptyState";

export default function History() {
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    listReviews()
      .then(async (res) => {
        if (!res.ok) {
          if (res.status === 401) navigate("/login", { replace: true });
          setError("Failed to load history");
          return;
        }
        setReviews(await res.json());
      })
      .catch(() => setError("Network error loading history"))
      .finally(() => setLoading(false));
  }, [navigate]);

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-56px)] flex items-center justify-center px-4">
        <ScanLoaderInline />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <EmptyState
          title="Unable to load history"
          subtitle={error}
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
    <div className="page">
      <div>
        <h2 className="section-title">Review history</h2>
        <p className="section-sub">
          Your past code reviews, newest first.
        </p>
      </div>

      {reviews.length === 0 ? (
        <EmptyState
          title="No reviews yet"
          subtitle="Submit some code to see your review history here."
          action={
            <Link to="/submit" className="btn btn-primary">
              Submit new code
            </Link>
          }
        />
      ) : (
        <div className="panel">
          <table className="history-table">
            <thead>
              <tr>
                <th className="w-16">ID</th>
                <th className="w-40">Language</th>
                <th className="w-24">Score</th>
                <th>Reviewed at</th>
                <th className="w-32">Code preview</th>
                <th className="w-24"></th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((r) => (
                <tr key={r.id}>
                  <td className="font-mono text-sm font-bold text-ink">#{r.id}</td>
                  <td className="font-mono text-sm text-slate-600">{r.language}</td>
                  <td className="text-sm font-bold">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      r.score >= 75
                        ? "bg-success-bg text-success border border-success/20"
                        : r.score >= 50
                        ? "bg-warn-bg text-warn border border-warn/20"
                        : "bg-danger-bg text-danger border border-danger/20"
                    }`}>
                      {r.score}
                    </span>
                  </td>
                  <td className="text-sm text-slate-500">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td>
                    <span className="history-code">{r.id}</span>
                  </td>
                  <td>
                    <Link
                      to={`/results/${r.id}`}
                      className="text-accent font-medium hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ScanLoaderInline() {
  return (
    <div className="loader">
      <div className="loader-dot" />
      <p className="loader-text">Loading history...</p>
    </div>
  );
}
