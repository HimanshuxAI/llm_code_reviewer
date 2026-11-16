import { Code } from "lucide-react";

interface DiffPreviewProps {
  source_code: string;
  fixed_snippet: string | null;
}

export default function DiffPreview({ source_code, fixed_snippet }: DiffPreviewProps) {
  return (
    <div className="panel p-6 fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Code className="h-4 w-4 text-blue-500" /> Original code
        </h2>
        {fixed_snippet && (
          <span className="badge badge-static text-xs px-2 py-0.5 border">Analyzed</span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-50 border border-white/80 rounded-xl overflow-hidden">
          <div className="px-3 py-2 bg-white/60 border-b border-white/80 text-xs font-mono text-slate-400 flex justify-between items-center">
            <span>Input</span>
            <span>{source_code.split("\n").length} lines</span>
          </div>
          <pre className="p-3 font-mono text-xs text-slate-600 overflow-x-auto">{source_code}</pre>
        </div>
        {fixed_snippet ? (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl overflow-hidden">
            <div className="px-3 py-2 bg-emerald-100/50 border-b border-emerald-200 text-xs font-mono text-emerald-600 flex justify-between items-center">
              <span>Suggested fix</span>
              <span className="text-emerald-500">Apply</span>
            </div>
            <pre className="p-3 font-mono text-xs text-emerald-800 overflow-x-auto">{fixed_snippet}</pre>
          </div>
        ) : null}
      </div>
    </div>
  );
}
