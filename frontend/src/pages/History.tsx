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
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4">
        <div className="flex flex-col items-center justify-center py-24">
          <div className="relative w-10 h-10 mb-4">
            <Clock className="h-5 w-5 text-blue-500 animate-spin" />
          </div>
          <p className="text-sm text-slate-500">Loading history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4">
        <div className="max-w-md">
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
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <div>
        <h1 className="h1">Review history</h1>
        <p className="mt-2 text-sm text-slate-500">
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
        <div className="panel p-0 shadow-lg overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-white/80">
                <th className="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest">ID</th>
                <th className="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Language</th>
                <th className="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Score</th>
                <th className="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Reviewed at</th>
                <th className="px-4 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/80">
              {reviews.map((r) => (
                <tr
                  key={r.id}
                  className="hover:bg-blue-25 transition-colors group"
                >
                  <td className="px-4 py-3 text-sm font-mono text-slate-700 font-medium">#{r.id}</td>
                  <td className="px-4 py-3 text-sm font-mono text-slate-700">{r.language}</td>
                  <td className="px-4 py-3 text-sm font-bold">
                    <span className={`px-2 py-1 rounded-xl text-xs font-bold ${
                      r.score >= 75
                        ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                        : r.score >= 50
                        ? "bg-amber-100 text-amber-700 border border-amber-200"
                        : "bg-red-100 text-red-700 border border-red-200"
                    }`}>
                      {r.score}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/results/${r.id}`}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
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
