import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listReviews } from "../api";
import { type ReviewSummary } from "../api";
import { Clock, Code2 } from "lucide-react";

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
        <Clock className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-red-600">{error}</p>
          <button onClick={() => navigate("/submit")} className="mt-4 btn">
            Submit new code
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Review history</h1>
        <p className="mt-1 text-sm text-gray-600">
          Your past code reviews, newest first.
        </p>
      </div>

      {reviews.length === 0 ? (
        <div className="panel p-12 text-center shadow-sm">
          <Code2 className="h-10 w-10 mx-auto text-gray-400 mb-3" />
          <h2 className="text-lg font-medium text-gray-900">No reviews yet</h2>
          <p className="mt-1 text-sm text-gray-600">
            Submit some code to see your review history here.
          </p>
          <button onClick={() => navigate("/submit")} className="mt-6 btn">
            Submit new code
          </button>
        </div>
      ) : (
        <div className="panel p-0 shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">ID</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Language</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Score</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Reviewed at</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase"></th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((r) => (
                <tr
                  key={r.id}
                  className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-gray-900 font-medium">#{r.id}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 font-mono">{r.language}</td>
                  <td className="px-4 py-3 text-sm font-semibold">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                      r.score >= 75
                        ? "bg-green-100 text-green-700"
                        : r.score >= 50
                        ? "bg-amber-100 text-amber-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {r.score}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/results/${r.id}`}
                      className="text-blue-600 hover:underline text-sm font-medium"
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
