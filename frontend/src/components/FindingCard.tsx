import SeverityBadge from "./SeverityBadge";

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
  const sourceColor =
    finding.source === "llm" ? "bg-blue-50 border-blue-100 text-blue-700" : "bg-gray-50 border-gray-100 text-gray-700";
  return (
    <div className="panel p-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
          {finding.rule_id} &bull; line {finding.line}
        </span>
        <SeverityBadge severity={finding.severity} />
        <span className={`text-xs px-2 py-0.5 rounded ${sourceColor}`}>
          {finding.source === "llm" ? "AI review" : "Static scan"}
        </span>
      </div>
      <h3 className="text-sm font-semibold text-gray-900 mb-1">{finding.title}</h3>
      <p className="text-sm text-gray-700 mb-3">{finding.explanation}</p>
      <div className="bg-white border border-gray-200 rounded-md p-3 mb-3">
        <p className="text-xs font-medium text-gray-500 mb-1">Suggested fix</p>
        <pre className="text-xs text-gray-900 font-mono overflow-x-auto whitespace-pre-wrap break-words">
          {finding.suggestion}
        </pre>
      </div>
      {finding.fixed_snippet && (
        <div className="bg-green-50 border border-green-100 rounded-md p-3">
          <p className="text-xs font-medium text-green-800 mb-1">Corrected snippet</p>
          <pre className="text-xs text-green-900 font-mono overflow-x-auto whitespace-pre-wrap break-words">
            {finding.fixed_snippet}
          </pre>
        </div>
      )}
    </div>
  );
}
