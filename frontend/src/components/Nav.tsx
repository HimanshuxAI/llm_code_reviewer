import { Link, useLocation, useNavigate } from "react-router-dom";
import { ShieldCheck, LogOut, History as HistoryIcon } from "lucide-react";

export default function Nav() {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("token");
  const active = (p: string) => location.pathname === p;

  return (
    <nav className="sticky top-0 z-40 border-b border-white/80 bg-white/70 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link
            to="/"
            className="flex items-center gap-2 font-extrabold text-white tracking-tighter"
            style={{ background: "linear-gradient(135deg, #0f172a 0%, #0ea5e9 100%)", WebkitTextFillColor: "transparent", backgroundClip: "text" }}
          >
            <ShieldCheck className="h-5 w-5 text-white" />
            <span>Code Reviewer</span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/history"
              className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                active("/history")
                  ? "bg-blue-50 border border-blue-200 text-blue-600 shadow-sm"
                  : "border-transparent text-slate-500 hover:bg-white hover:text-blue-600"
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
                className="px-3 py-2 rounded-xl text-sm font-medium text-slate-500 transition-all hover:bg-white hover:text-blue-600 border-transparent"
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
