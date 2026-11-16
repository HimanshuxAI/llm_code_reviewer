import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listReviews } from "../api";
import { type ReviewSummary } from "../api";
import { Clock } from "lucide-react";
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
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <div className="flex flex-col items-center justify-center py-20">
          <div className="relative w-10 h-10 mb-4">
            <Clock className="h-5 w-5 text-blue-400 animate-spin" />
          </div>
          <p className="text-sm text-slate-400">Loading history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4">
        <EmptyState
          title="Unable to load history"
          subtitle={error}
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
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Review history</h1>
        <p className="mt-1 text-sm text-slate-400">
          Your past code reviews, newest first.
        </p>
      </div>

      {reviews.length === 0 ? (
        <EmptyState
          title="No reviews yet"
          subtitle="Submit some code to see your review history here."
          action={
            <button
              onClick={() => navigate("/submit")}
              className="btn btn-primary"
            >
              Submit new code
            </button>
          }
        />
      ) : (
        <div className="panel p-0 shadow-2xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/50 border-b border-white/5">
                <th className="px-4 py-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">ID</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Language</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Score</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Reviewed at</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-slate-400 uppercase tracking-wider"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {reviews.map((r) => (
                <tr
                  key={r.id}
                  className="hover:bg-white/5 transition-colors group"
                >
                  <td className="px-4 py-3 text-sm font-mono text-slate-300 font-medium">#{r.id}</td>
                  <td className="px-4 py-3 text-sm font-mono text-slate-200">{r.language}</td>
                  <td className="px-4 py-3 text-sm font-bold">
                    <span className={`px-2 py-1 rounded-md text-xs font-bold ${
                      r.score >= 75
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : r.score >= 50
                        ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        : "bg-red-500/10 text-red-400 border border-red-500/20"
                    }`}>
                      {r.score}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/results/${r.id}`}
                      className="text-blue-400 hover:text-blue-300 text-sm font-medium"
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
