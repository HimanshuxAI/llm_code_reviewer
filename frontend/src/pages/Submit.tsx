import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitReview } from "../api";
import { Upload, ArrowRight } from "lucide-react";
import CodeEditor from "../components/CodeEditor";

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
      const text = ev.target?.result as string;
      setCode(text);
      setFilename(file.name);
    };
    reader.readAsText(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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

  return (
    <div className="page">
      <div className="flex flex-col lg:flex-row gap-8 items-start">
        <div className="lg:w-3/5 min-w-0">
          <div>
            <h2 className="section-title">New review</h2>
            <p className="section-sub">
              Paste or upload source code. It gets scanned for bugs, security
              issues, and quality problems — then scored 0-100.
            </p>
          </div>

          <div className="mt-6 panel p-4">
            <div className="flex items-center justify-between mb-4">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Source code</label>
              <button
                type="button"
                onClick={() => document.getElementById("file-input")?.click()}
                className="btn btn-ghost text-xs px-2 py-1"
              >
                <Upload className="h-3 w-3 mr-1" /> Upload file
              </button>
              <input
                id="file-input"
                type="file"
                className="hidden"
                accept=".py,.js,.jsx,.ts,.tsx,.java,.c,.cpp,.cc,.h,.hpp"
                onChange={handleFile}
              />
            </div>

            <CodeEditor value={code} onChange={setCode} filename={filename} />

            {filename && (
              <p className="text-[10px] text-slate-400 font-mono mt-2">File: {filename}</p>
            )}

            {error && (
              <div className="rounded bg-red-50 border border-red-100 px-3 py-2 text-sm text-red-700 mt-3">
                {error}
              </div>
            )}

            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading || !code.trim()}
              className="btn mt-4 w-full btn-primary"
            >
              <ArrowRight className="h-4 w-4 mr-2" /> Review code
            </button>
          </div>
        </div>

        <div className="lg:w-2/5">
          <div className="panel p-6 sticky top-24">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">How it works</h3>
            <ul className="space-y-4 text-sm text-slate-600">
              <li className="flex items-start gap-3">
                <span className="text-accent font-bold">1</span>
                Static heuristic scan runs on every submission — no API key needed.
              </li>
              <li className="flex items-start gap-3">
                <span className="text-accent font-bold">2</span>
                LLM review adds context-aware findings when configured.
              </li>
              <li className="flex items-start gap-3">
                <span className="text-accent font-bold">3</span>
                Findings are merged, deduplicated, and scored 0-100.
              </li>
            </ul>
          </div>
        </div>
      </div>

      <p className="mt-8 text-[11px] text-slate-400 max-w-md">
        Static analysis is always on. LLM review is used when an API key is
        configured on the backend.
      </p>
    </div>
  );
}
