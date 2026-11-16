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
  return (
    <article className="finding fade-in">
      <div className="finding-header">
        <div className="finding-meta">
          <span className="finding-id">{finding.rule_id}</span>
          <span className="finding-line">line {finding.line}</span>
          <span className={`finding-source ${finding.source}`}>
            {finding.source === "llm" ? "ai review" : "static scan"}
          </span>
        </div>
        <SeverityBadge severity={finding.severity} />
      </div>

      <h3 className="finding-title">{finding.title}</h3>
      <p className="finding-explain">{finding.explanation}</p>

      <div className="fixing">
        <div>
          <span className="fixing-label">Suggested fix</span>
          <pre className="fixing-content suggest">{finding.suggestion}</pre>
        </div>
        {finding.fixed_snippet && (
          <div>
            <span className="fixing-label">Corrected snippet</span>
            <pre className="fixing-content fixed">{finding.fixed_snippet}</pre>
          </div>
        )}
      </div>
    </article>
  );
}
