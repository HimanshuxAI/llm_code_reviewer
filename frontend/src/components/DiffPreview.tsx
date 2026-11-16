import { Code } from "lucide-react";

interface DiffPreviewProps {
  source_code: string;
  fixed_snippet: string | null;
}

export default function DiffPreview({ source_code, fixed_snippet }: DiffPreviewProps) {
  return (
    <div className="panel p-6 fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Code className="h-4 w-4 text-blue-400" /> Original code
        </h2>
        {fixed_snippet && (
          <span className="badge badge-static text-xs px-2 py-0.5 border">Analyzed</span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-black/40 border border-white/5 rounded-lg overflow-hidden">
          <div className="px-3 py-2 bg-slate-900/50 border-b border-white/5 text-xs font-mono text-slate-500 flex justify-between items-center">
            <span>Input</span>
            <span>{source_code.split("\n").length} lines</span>
          </div>
          <pre className="p-3 font-mono text-xs text-slate-300 overflow-x-auto">{source_code}</pre>
        </div>
        {fixed_snippet ? (
          <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg overflow-hidden">
            <div className="px-3 py-2 bg-emerald-500/10 border-b border-emerald-500/30 text-xs font-mono text-emerald-400 flex justify-between items-center">
              <span>Suggested fix</span>
              <span className="text-emerald-500">Apply</span>
            </div>
            <pre className="p-3 font-mono text-xs text-emerald-100 overflow-x-auto">{fixed_snippet}</pre>
          </div>
        ) : null}
      </div>
    </div>
  );
}
