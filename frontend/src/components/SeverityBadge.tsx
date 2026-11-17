interface SeverityBadgeProps { severity: string; }

const STYLE: Record<string, string> = {
  critical: "critical",
  high: "high",
  medium: "medium",
  low: "low",
};

/* Rubber-stamp severity badge: uppercase text, 1.5px border in the severity
   color, tilted -2deg (see .severity in index.css). */
export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const cls = STYLE[severity.toLowerCase()] || "low";
  return <span className={`severity ${cls}`}>{severity.charAt(0).toUpperCase() + severity.slice(1)}</span>;
}
