import { Link, useLocation, useNavigate } from "react-router-dom";
import { ShieldCheck, LogOut, History as HistoryIcon } from "lucide-react";

export default function Nav() {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("token");
  const active = (p: string) => location.pathname === p;

  return (
    <nav className="fixed top-0 left-0 right-0 z-40 border-b border-white/5 bg-black/60 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link
            to="/"
            className="flex items-center gap-2 font-bold text-white tracking-tight"
          >
            <ShieldCheck className="h-5 w-5 text-blue-400" />
            <span>Code Reviewer</span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/history"
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                active("/history")
                  ? "bg-blue-500/10 border border-blue-500/30 text-blue-400"
                  : "border-transparent text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <HistoryIcon className="h-4 w-4 mr-1.5" /> History
            </Link>

            {token ? (
              <button
                onClick={() => {
                  localStorage.removeItem("token");
                  navigate("/login");
                }}
                className="px-3 py-2 rounded-lg text-sm font-medium text-slate-400 transition-all hover:bg-white/5 hover:text-white border-transparent"
              >
                <LogOut className="h-4 w-4 mr-1.5" /> Sign out
              </button>
            ) : (
              <>
                <Link to="/login" className="btn-outline px-3 py-1.5 text-sm font-medium">Sign in</Link>
                <Link to="/register" className="btn-primary px-3 py-1.5 text-sm font-medium">Create account</Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
