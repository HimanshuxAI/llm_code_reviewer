import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitReview } from "../api";
import { Upload, Play, FileCode2 } from "lucide-react";
import Workspace from "../components/Workspace";

export default function Submit() {
  const [code, setCode] = useState("");
  const [filename, setFilename] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setCode(ev.target?.result as string);
      setFilename(file.name);
    };
    reader.readAsText(file);
  };

  const handleSubmit = async () => {
    setError("");
    if (!code.trim()) {
      setError("Paste or upload some source code first.");
      return;
    }
    setLoading(true);
    try {
      const res = await submitReview({ source_code: code, filename });
      if (!res.ok) {
        setError("Review failed. Please try again.");
        return;
      }
      const review = await res.json();
      navigate(`/results/${review.id}`);
    } catch {
      setError("Network error. Is the backend running on localhost:8000?");
    } finally {
      setLoading(false);
    }
  };

  const lines = code.split("\n");

  return (
    <Workspace
      tab={filename || "untitled.py"}
      status={{
        left: code ? `${lines.length} lines · ${code.length} chars` : "no file open",
        right: filename ? filename.split(".").pop() : "plaintext",
      }}
      tree={
        <>
          <div className="tree-head">Explorer</div>
          <div className="tree-folder">
            <FileCode2 className="h-3.5 w-3.5" /> workspace
          </div>
          {code ? (
            <div className="tree-item active">{filename || "untitled.py"}</div>
          ) : (
            <div className="tree-item" style={{ color: "var(--muted)", cursor: "default" }}>
              no file open
            </div>
          )}
        </>
      }
      inspector={
        <>
          <div className="inspector-head">
            <span className="inspector-title">Review</span>
          </div>
          <div className="inspector-body">
            <button
              onClick={handleSubmit}
              disabled={loading || !code.trim()}
              className="btn btn-primary w-full"
            >
              <Play className="h-4 w-4 mr-2" />
              {loading ? "Analyzing..." : "Run review"}
            </button>

            <button
              onClick={() => document.getElementById("file-input")?.click()}
              className="btn btn-ghost w-full"
            >
              <Upload className="h-4 w-4 mr-2" /> Load file
            </button>
            <input
              id="file-input"
              type="file"
              className="hidden"
              accept=".py,.js,.jsx,.ts,.tsx,.java,.c,.cpp,.cc,.h,.hpp"
              onChange={handleFile}
            />

            {error && <div className="form-error">{error}</div>}

            <div style={{ borderTop: "1px solid var(--line)", paddingTop: 14, marginTop: 6 }}>
              <p className="inspector-title mb-3">Pipeline</p>
              <ol style={{ listStyle: "none", padding: 0 }} className="space-y-2">
                {[
                  "Detect language",
                  "Regex security rules",
                  "Taint tracking (source to sink)",
                  "Secret detection & quality",
                ].map((step, i) => (
                  <li
                    key={step}
                    style={{
                      display: "flex",
                      gap: 9,
                      fontSize: 12,
                      color: "var(--ink-soft)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    <span style={{ color: "var(--accent)", fontWeight: 700 }}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </>
      }
    >
      <div className="ide-editor">
        <div className="ide-gutter">
          {lines.map((_, i) => (
            <div key={i} className="ide-gutter-line">
              {i + 1}
            </div>
          ))}
        </div>
        <div className="ide-code">
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={"# paste your code here\n\ndef login(user, password):\n    ..."}
            spellCheck={false}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
          />
        </div>
      </div>
    </Workspace>
  );
}
