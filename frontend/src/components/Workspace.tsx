import { Link, useNavigate, useLocation } from "react-router-dom";
import { FileCode2, History as HistoryIcon, ShieldCheck, LogOut, Plus } from "lucide-react";

interface WorkspaceProps {
  children: React.ReactNode;
  tree?: React.ReactNode;
  inspector?: React.ReactNode;
  tab?: string;
  status?: { left?: string; right?: string; score?: number };
  hideTree?: boolean;
  hideInspector?: boolean;
}

export default function Workspace({
  children,
  tree,
  inspector,
  tab,
  status,
  hideTree,
  hideInspector,
}: WorkspaceProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("token");

  const classes = ["ide"];
  if (hideTree) classes.push("no-tree");
  if (hideInspector) classes.push("no-inspector");
  if (hideTree && hideInspector) classes.push("only-main");

  return (
    <div className={classes.join(" ")}>
      <div className="rail">
        <Link to="/" className="rail-logo" title="Code Reviewer" />
        <button
          className="rail-item"
          onClick={() => navigate("/submit")}
          title="New review"
        >
          <Plus className="h-5 w-5" />
        </button>
        <button
          className={`rail-item ${location.pathname === "/history" ? "active" : ""}`}
          onClick={() => navigate("/history")}
          title="Review history"
        >
          <HistoryIcon className="h-5 w-5" />
        </button>
        <button
          className={`rail-item ${location.pathname === "/submit" ? "active" : ""}`}
          onClick={() => navigate("/submit")}
          title="Editor"
        >
          <FileCode2 className="h-5 w-5" />
        </button>
        <div className="rail-spacer" />
        {token && (
          <button
            className="rail-item"
            onClick={() => {
              localStorage.removeItem("token");
              navigate("/login");
            }}
            title="Sign out"
          >
            <LogOut className="h-5 w-5" />
          </button>
        )}
      </div>

      {!hideTree && <div className="tree">{tree}</div>}

      <div className="ide-main">
        {tab && (
          <div className="ide-tabs">
            <div className="ide-tab active">
              <FileCode2 className="h-3.5 w-3.5" />
              {tab}
            </div>
          </div>
        )}
        {children}
      </div>

      {!hideInspector && <div className="inspector">{inspector}</div>}

      <div className="statusbar">
        <div className="status-left">
          <span className="status-item">
            <ShieldCheck className="h-3 w-3" /> code-reviewer
          </span>
          {status?.left && <span>{status.left}</span>}
        </div>
        <div className="status-right">
          {status?.right && <span>{status.right}</span>}
          {status?.score !== undefined && (
            <span className="status-score">score {status.score}/100</span>
          )}
        </div>
      </div>
    </div>
  );
}
