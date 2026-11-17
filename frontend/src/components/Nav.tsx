import { Link, useLocation, useNavigate } from "react-router-dom";
import { History as HistoryIcon } from "lucide-react";
import { token as getToken, clearToken } from "../api";

export default function Nav() {
  const navigate = useNavigate();
  const location = useLocation();
  const token = getToken();
  const active = (p: string) => location.pathname === p;

  return (
    <div className="topbar">
      <div className="topbar-inner">
        <Link to="/" className="brand">
          <div className="brand-mark" />
          <span>Code Reviewer</span>
        </Link>

        <div className="nav-links">
          <Link
            to="/history"
            className={`nav-link ${active("/history") ? "active" : ""}`}
          >
            <HistoryIcon className="h-4 w-4 mr-1" /> History
          </Link>

          {token ? (
            <button
              onClick={() => {
                clearToken();
                navigate("/login");
              }}
              className="btn btn-ghost"
            >
              Sign out
            </button>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost">Sign in</Link>
              <Link to="/register" className="btn btn-primary">Create account</Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
