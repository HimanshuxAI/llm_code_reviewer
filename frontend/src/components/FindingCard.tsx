import SeverityBadge from "./SeverityBadge";
import { AlertTriangle, Zap, Code } from "lucide-react";

const SOURCE_ICON: Record<string, React.ElementType> = {
  static: Zap,
  llm: AlertTriangle,
};

interface FindingCardProps {
  finding: {
    rule_id: string;
    title: string;
    severity: string;
    line: number;
    explanation: string;
    suggestion: string;
    source: string;
    fixed_snippet: string | null;
  };
}

export default function FindingCard({ finding }: FindingCardProps) {
  const Icon = SOURCE_ICON[finding.source] || Code;
  const isLlm = finding.source === "llm";

  return (
    <article className="panel p-5 fade-in border-l-3 pl-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-400 uppercase tracking-wider">
          <Icon className={`h-3 w-3 ${isLlm ? "text-purple-500" : "text-blue-500"}`} />
          <span>{finding.rule_id}</span>
          <span>line {finding.line}</span>
        </div>
        <div className="flex items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <span className={`badge text-xs px-2 py-0.5 border ${isLlm ? "badge-llm" : "badge-static"}`}>
            {finding.source === "llm" ? "AI review" : "Static scan"}
          </span>
        </div>
      </div>

      <h3 className="text-sm font-bold text-slate-800 mb-1">{finding.title}</h3>
      <p className="text-sm text-slate-600 mb-3 leading-relaxed">{finding.explanation}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-50 border border-white/80 rounded-xl p-3">
          <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Suggested fix</p>
          <pre className="text-xs font-mono text-slate-700 overflow-x-auto whitespace-pre-wrap break-words">{finding.suggestion}</pre>
        </div>
        {finding.fixed_snippet ? (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3">
            <p className="text-[10px] font-bold text-emerald-600 uppercase mb-1">Corrected snippet</p>
            <pre className="text-xs font-mono text-emerald-800 overflow-x-auto whitespace-pre-wrap break-words">{finding.fixed_snippet}</pre>
          </div>
        ) : null}
      </div>
    </article>
  );
}
