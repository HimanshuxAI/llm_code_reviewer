import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listReviews } from "../api";
import { type ReviewSummary } from "../api";
import Workspace from "../components/Workspace";
import EmptyState from "../components/EmptyState";
import { FileCode2, Plus } from "lucide-react";

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
      <div className="min-h-screen flex items-center justify-center">
        <div className="loader">
          <div className="loader-dot" />
          <p className="loader-text">Loading history...</p>
        </div>
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

  const avg = reviews.length
    ? Math.round(reviews.reduce((sum, r) => sum + r.score, 0) / reviews.length)
    : 0;

  return (
    <Workspace
      tab="history.json"
      hideInspector
      status={{
        left: `${reviews.length} reviews`,
        right: `average ${avg}/100`,
      }}
      tree={
        <>
          <div className="tree-head">Reviews</div>
          <div className="tree-folder">
            <FileCode2 className="h-3.5 w-3.5" /> submissions
          </div>
          {reviews.map((r) => (
            <Link key={r.id} to={`/results/${r.id}`} className="tree-item">
              <span>review-{r.id}</span>
              <span
                className={`tree-badge ${
                  r.score >= 75 ? "ok" : r.score >= 50 ? "warn" : "crit"
                }`}
              >
                {r.score}
              </span>
            </Link>
          ))}
        </>
      }
    >
      <div style={{ padding: 24, overflow: "auto" }}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-ink">
              Review history
            </h1>
            <p className="text-sm text-ink-soft mt-1">
              Every submission you have made, newest first.
            </p>
          </div>
          <Link to="/submit" className="btn btn-primary">
            <Plus className="h-4 w-4 mr-1.5" /> New review
          </Link>
        </div>

        {reviews.length === 0 ? (
          <EmptyState
            title="No reviews yet"
            subtitle="Submit some code and it will show up here with its score."
            action={
              <Link to="/submit" className="btn btn-primary">
                Submit new code
              </Link>
            }
          />
        ) : (
          <div className="panel" style={{ overflow: "hidden" }}>
            <table className="history-table">
              <thead>
                <tr>
                  <th style={{ width: 70 }}>ID</th>
                  <th style={{ width: 130 }}>Language</th>
                  <th style={{ width: 100 }}>Score</th>
                  <th>Reviewed at</th>
                  <th style={{ width: 90 }}></th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((r) => (
                  <tr key={r.id}>
                    <td className="font-mono text-sm font-bold text-ink">#{r.id}</td>
                    <td className="font-mono text-sm text-ink-soft">{r.language}</td>
                    <td>
                      <span
                        className={`px-2 py-1 rounded text-xs font-bold ${
                          r.score >= 75
                            ? "bg-success-bg text-success border border-success-border"
                            : r.score >= 50
                            ? "bg-warn-bg text-warn border border-warn-border"
                            : "bg-danger-bg text-danger border border-danger-border"
                        }`}
                      >
                        {r.score}
                      </span>
                    </td>
                    <td className="text-sm text-muted">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td>
                      <Link
                        to={`/results/${r.id}`}
                        className="text-primary font-medium hover:underline text-sm"
                      >
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Workspace>
  );
}
