interface SeverityBadgeProps { severity: string; }

const STYLE: Record<string, string> = {
  critical: "severity critical",
  high: "severity high",
  medium: "severity medium",
  low: "severity low",
};

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const cls = STYLE[severity.toLowerCase()] || "severity low";
  return <span className={`severity ${cls}`}>{severity.charAt(0).toUpperCase() + severity.slice(1)}</span>;
}
