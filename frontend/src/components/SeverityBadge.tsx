interface SeverityBadgeProps { severity: string; }

const STYLE: Record<string, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
};

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const cls = STYLE[severity.toLowerCase()] || "badge-low";
  return <span className={`badge ${cls}`}>{severity.charAt(0).toUpperCase() + severity.slice(1)}</span>;
}
