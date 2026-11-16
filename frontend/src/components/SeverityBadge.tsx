interface SeverityBadgeProps {
  severity: string;
}

const STYLE: Record<string, string> = {
  critical: "border-red-200 bg-red-50 text-red-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-gray-200 bg-gray-50 text-gray-700",
};

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const cls = STYLE[severity.toLowerCase()] || STYLE.low;
  return (
    <span className={`badge border ${cls}`}>{severity.charAt(0).toUpperCase() + severity.slice(1)}</span>
  );
}
