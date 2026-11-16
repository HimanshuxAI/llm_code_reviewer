interface ScoreDonutProps { score: number; }

const getColor = (score: number) => {
  if (score >= 90) return { color: "text-emerald-600", border: "border-emerald-500/20", bg: "bg-emerald-50", label: "Excellent" };
  if (score >= 75) return { color: "text-emerald-600", border: "border-emerald-500/20", bg: "bg-emerald-50", label: "Great" };
  if (score >= 50) return { color: "text-amber-600", border: "border-amber-500/20", bg: "bg-amber-50", label: "Fair" };
  if (score >= 25) return { color: "text-orange-600", border: "border-orange-500/20", bg: "bg-orange-50", label: "Needs work" };
  return { color: "text-red-600", border: "border-red-500/20", bg: "bg-red-50", label: "Critical" };
};

export default function ScoreDonut({ score }: ScoreDonutProps) {
  const { color, border, bg, label } = getColor(score);
  const circumference = 2 * Math.PI * 26;
  const offset = circumference * (1 - Math.max(0, Math.min(100, score)) / 100);
  const colorClass = color === "text-emerald-600" ? "text-emerald-600" : color === "text-amber-600" ? "text-amber-600" : color === "text-orange-600" ? "text-orange-600" : "text-red-600";

  return (
    <div className="panel p-6 fade-in">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Code quality score</p>
          <p className={`text-4xl font-extrabold ${colorClass}`}>{Math.max(0, score)}</p>
        </div>
        <span className={`px-3 py-1.5 rounded-xl text-xs font-bold border ${border} ${bg}`}>
          {label}
        </span>
      </div>
      <div className="relative w-28 h-28 mx-auto mb-3">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="26" fill="none" stroke="#f1f5f9" strokeWidth="5" />
          <circle
            cx="28"
            cy="28"
            r="26"
            fill="none"
            stroke="currentColor"
            strokeWidth="5"
            strokeLinecap="round"
            className={colorClass}
            style={{ strokeDasharray: circumference, strokeDashoffset: offset, transition: "stroke-dashoffset 0.8s ease-out" }}
          />
        </svg>
      </div>
      <p className="text-xs text-slate-500 text-center">Severity-weighted. 0-100.</p>
    </div>
  );
}
