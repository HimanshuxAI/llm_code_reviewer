import { Link, useNavigate, useLocation } from "react-router-dom";
import { LogOut, ShieldCheck, History as HistoryIcon } from "lucide-react";
import { token } from "../api";

export default function Nav() {
  const navigate = useNavigate();
  const location = useLocation();
  const authed = !!token();

  const href = (p: string) => location.pathname === p;

  return (
    <nav className="sticky top-0 z-20 border-b border-gray-200 bg-white/90 backdrop-blur">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-12">
          <Link to="/" className="flex items-center gap-2 font-semibold text-gray-900">
            <ShieldCheck className="h-5 w-5 text-blue-600" />
            <span className="tracking-tight">Code Reviewer</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              to="/history"
              className={`px-3 py-1.5 text-sm font-medium rounded-md border ${
                href("/history")
                  ? "bg-blue-50 border-blue-200 text-blue-700"
                  : "border-transparent text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <HistoryIcon className="h-4 w-4 mr-1.5" /> History
            </Link>
            {authed ? (
              <button
                onClick={() => {
                  localStorage.removeItem("token");
                  navigate("/login");
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded-md"
              >
                <LogOut className="h-4 w-4" /> Sign out
              </button>
            ) : (
              <>
                <Link to="/login" className="btn-outline px-3 py-1.5 text-sm font-medium">Sign in</Link>
                <Link to="/register" className="btn px-3 py-1.5 text-sm font-medium">Create account</Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
