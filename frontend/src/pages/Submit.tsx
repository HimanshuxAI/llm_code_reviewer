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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">New review</h1>
        <p className="mt-1 text-sm text-slate-400">
          Paste or upload source code. We scan it for bugs, security issues, and
          quality problems, then score it from 0 to 100.
        </p>
      </div>

      <div className="panel p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-semibold text-slate-300">Source code</label>
          <button
            type="button"
            onClick={() => document.getElementById("file-input")?.click()}
            className="btn-outline px-3 py-1.5 text-xs font-medium"
          >
            <Upload className="h-3 w-3 mr-1.5" /> Upload file
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
          <p className="text-[10px] text-slate-500 font-mono">File: {filename}</p>
        )}

        {error && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleSubmit}
          disabled={loading || !code.trim()}
          className="btn w-full btn-primary"
        >
          <ArrowRight className="h-4 w-4 mr-2" /> Review code
        </button>
      </div>

      <div className="text-[11px] text-slate-500 max-w-md">
        Static analysis is always on. LLM review is used when an API key is
        configured on the backend.
      </div>
    </div>
  );
}
